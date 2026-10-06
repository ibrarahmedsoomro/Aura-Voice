import os
import uuid
import asyncio
from typing import List, Dict, Optional, Callable, Any
from datetime import datetime

from ..models.schemas import (
    ProjectState, GenerateVoiceRequest, RedoChunkRequest,
    ChunkPlan, QCResult, VoiceProfile, ProjectCharacter, ScenePlan
)
from ..database.db import DatabaseManager
from ..core.voice_catalog import (
    VOICE_CATALOG, find_voice_by_id_or_profile,
    rank_voices_for_script, verify_voice_consent_and_policy
)
from ..providers.edge_provider import EdgeTTSProvider
from ..agents.script_intelligence import ScriptIntelligenceAgent
from ..agents.speech_planner import SpeechPlannerAgent
from ..agents.emotion_performance import EmotionPerformanceAgent
from ..agents.pronunciation import PronunciationAgent
from ..agents.audio_processor import AudioProcessorAgent
from ..agents.qc_agent import AutonomousQCAgent
from ..agents.repair_agent import AutonomousRepairAgent
from ..agents.timing_alignment import TimingAlignmentAgent
from ..agents.memory_agent import ProjectMemoryAgent as MemoryAgent

class CentralOrchestrator:
    """
    Module 1: Central Orchestrator & Autonomous Voice Agent Engine.
    Executes the 9-step production pipeline:
    Script -> Speaker/Scene segmentation -> Character mapping -> Voice casting (Auto Cast 2.0)
    -> Performance planning -> Chunk generation -> Audio assembly -> Mastering -> QC.
    Provides targeted single-line redo without full-project regeneration.
    """

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.storage_dir = os.path.join(base_dir, "storage")
        self.exports_dir = os.path.join(base_dir, "exports")
        os.makedirs(self.storage_dir, exist_ok=True)
        os.makedirs(self.exports_dir, exist_ok=True)

        self.db = db_manager or DatabaseManager()
        self.tts_provider = EdgeTTSProvider()
        self.script_agent = ScriptIntelligenceAgent()
        self.pronunciation_agent = PronunciationAgent()
        self.emotion_agent = EmotionPerformanceAgent()
        self.speech_planner = SpeechPlannerAgent(self.emotion_agent, self.pronunciation_agent, self.script_agent)
        self.audio_processor = AudioProcessorAgent()
        self.qc_agent = AutonomousQCAgent()
        self.repair_agent = AutonomousRepairAgent(self.tts_provider, self.audio_processor, self.qc_agent)
        self.timing_agent = TimingAlignmentAgent()
        self.memory_agent = MemoryAgent(self.storage_dir)

        self.cancelled_projects = set()

    def cancel_project(self, project_id: str):
        self.cancelled_projects.add(project_id)

    def _setup_project_storage(self, project_id: str) -> Dict[str, str]:
        p_raw = os.path.join(self.storage_dir, project_id, "raw")
        p_proc = os.path.join(self.storage_dir, project_id, "processed")
        p_final = os.path.join(self.exports_dir, project_id, "final")
        p_subs = os.path.join(self.exports_dir, project_id, "subtitles")

        os.makedirs(p_raw, exist_ok=True)
        os.makedirs(p_proc, exist_ok=True)
        os.makedirs(p_final, exist_ok=True)
        os.makedirs(p_subs, exist_ok=True)

        return {"raw": p_raw, "processed": p_proc, "final": p_final, "subtitles": p_subs}

    async def execute_voice_pipeline(
        self,
        request: GenerateVoiceRequest,
        existing_project_id: Optional[str] = None,
        progress_callback: Optional[Callable[[ProjectState], Any]] = None
    ) -> ProjectState:
        project_id = existing_project_id or f"VX-{uuid.uuid4().hex[:6].upper()}"
        if project_id in self.cancelled_projects:
            self.cancelled_projects.remove(project_id)

        paths = self._setup_project_storage(project_id)

        state = ProjectState(
            project_id=project_id,
            title=request.topic_prompt or (request.text[:40].strip() + "..."),
            raw_input=request.text,
            original_text=request.text,
            input_mode="text" if not request.topic_prompt else "topic",
            emotion_mode=request.emotion_mode or "auto"
        )
        self._sync_state_to_db(state)

        # STEP 1: Script Intelligence & Normalization
        state.status = "UNDERSTANDING"
        state.progress_percentage = 10
        state.current_step_description = "Analyzing script structure & normalizing text ✓"
        if progress_callback:
            await progress_callback(state)

        norm_text, detected_code, lang_desc = self.script_agent.normalize(request.text)
        if request.language_hint and request.language_hint != "auto":
            if request.language_hint == "en" and detected_code in ["roman_urdu", "roman_sindhi", "ur", "sd"]:
                lang_code = detected_code
            else:
                lang_code = request.language_hint
        else:
            lang_code = detected_code
        state.detected_language = lang_code

        # STEP 2: Voice Consent Gate & Casting Strategy
        state.status = "PLANNING"
        state.progress_percentage = 20
        state.current_step_description = "Verifying voice licensing & consent gate ✓"
        if progress_callback:
            await progress_callback(state)

        target_voice = None
        if request.voice_id and request.voice_id != "auto":
            consent = verify_voice_consent_and_policy(request.voice_id)
            if not consent["allowed"]:
                raise PermissionError(consent["reason"])
            target_voice = find_voice_by_id_or_profile(request.voice_id)

        # Smart Language-Voice Alignment:
        # If the script is Urdu, Roman Urdu, Sindhi, or Roman Sindhi, but target_voice is an English-only voice,
        # redirect to the optimal native Urdu/Sindhi voice so it speaks with authentic native pronunciation.
        if (not target_voice or (target_voice.language == "en" and lang_code in ["ur", "roman_urdu", "sd", "roman_sindhi"])):
            ranked = rank_voices_for_script(
                language=lang_code,
                style_preference=request.style_preference or (target_voice.style if target_voice else "Cinematic"),
                user_preferred_voice=self.db.get_preference("preferred_voice_id")
            )
            target_voice = ranked[0]["voice"]

        state.voice_profile = target_voice

        # STEP 3: Multi-Character Segmentation & Auto Cast 2.0 (Step 4, 6, 7)
        state.status = "CASTING"
        state.progress_percentage = 30
        state.current_step_description = "Detecting characters & Auto-Casting voices ✓"
        if progress_callback:
            await progress_callback(state)

        scenes, turns = self.speech_planner.extract_scenes_and_turns(norm_text)
        unique_speakers = list(dict.fromkeys([t["speaker"] for t in turns if t.get("speaker")]))

        # Load existing project characters to guarantee voice consistency
        existing_chars_data = self.db.get_project_characters(project_id)
        existing_chars = [ProjectCharacter(**cd) for cd in existing_chars_data] if existing_chars_data else []

        characters_map = self.speech_planner.auto_cast_characters(
            speakers=unique_speakers,
            language=lang_code,
            style_preference=request.style_preference or "Cinematic",
            existing_characters=existing_chars,
            locked_characters=request.locked_characters,
            character_overrides=request.character_overrides,
            default_voice_id=target_voice.voice_id
        )

        # Save characters to SQLite
        self.db.save_characters(project_id, [c.dict() for c in characters_map.values()])
        state.characters = list(characters_map.values())

        # STEP 4: Performance Planning & Prosody Direction (Step 8, 9, 10)
        state.progress_percentage = 40
        state.current_step_description = "Directing performance pacing & scene emotion ✓"

        scenes, chunks = self.speech_planner.plan_speech(
            normalized_text=norm_text,
            emotion_mode=request.emotion_mode or "auto",
            custom_pronunciations=request.custom_pronunciations,
            base_voice_id=target_voice.voice_id,
            language=lang_code,
            style_preference=request.style_preference or "Cinematic",
            characters_map=characters_map
        )
        state.scenes = scenes
        state.chunks = chunks
        self.db.save_scenes(project_id, [s.dict() for s in scenes])
        self._sync_state_to_db(state)
        if progress_callback:
            await progress_callback(state)

        # STEP 5: Chunk Speech Synthesis
        state.status = "SYNTHESIZING"
        total_chunks = len(chunks)

        for i, chunk in enumerate(chunks):
            if project_id in self.cancelled_projects:
                state.status = "CANCELLED"
                state.current_step_description = "Generation cancelled"
                self._sync_state_to_db(state)
                return state

            chunk_filename = f"chunk_{chunk.chunk_index:03d}.mp3"
            chunk_file = os.path.join(paths["raw"], chunk_filename)
            chunk.audio_file = chunk_file
            chunk.audio_path = chunk_file

            # Use assigned character voice if multi-character dialogue, else target voice
            chunk_voice = chunk.voice_id or chunk.assigned_voice_id or target_voice.voice_id
            chunk.voice_id = chunk_voice
            chunk.assigned_voice_id = chunk_voice

            res = await self.tts_provider.synthesize_chunk(
                text=chunk.spoken_text or chunk.normalized_text,
                voice_id=chunk_voice,
                rate=chunk.rate,
                pitch=chunk.pitch,
                output_path=chunk_file
            )

            if res["success"]:
                chunk.duration = self.audio_processor.get_audio_duration(chunk_file)
            else:
                chunk.duration = 0.0
                chunk.qc_pass = False
                chunk.qc_message = res.get("error")

            # Persist chunk to database
            self._save_chunk_to_db(project_id, chunk)

            pct = 40 + int(((i + 1) / total_chunks) * 30)
            state.progress_percentage = min(70, pct)
            state.current_step_description = f"Generating voices... {i + 1} / {total_chunks} lines synthesized"
            if progress_callback:
                await progress_callback(state)

        # STEP 6: Autonomous Quality Control Check (Step 12)
        state.status = "QC_RUNNING"
        state.progress_percentage = 75
        state.current_step_description = "Running quality check & pronunciation verification..."
        if progress_callback:
            await progress_callback(state)

        qc_report = self.qc_agent.run_full_qc(chunks)
        state.qc_report = qc_report
        self.db.save_qc_report(project_id, qc_report.dict())

        # STEP 7: Targeted Surgical Repair Loop (if any chunk failed)
        if not qc_report.overall_pass and qc_report.failed_chunk_indices:
            state.status = "REPAIRING"
            state.current_step_description = f"Repairing {len(qc_report.failed_chunk_indices)} line(s)..."
            if progress_callback:
                await progress_callback(state)

            for failed_idx in qc_report.failed_chunk_indices:
                target_chunk = next((c for c in chunks if c.chunk_index == failed_idx), None)
                if target_chunk:
                    reason = qc_report.repair_suggestions.get(failed_idx, "Cadence anomaly")
                    v_to_use = target_chunk.voice_id or target_chunk.assigned_voice_id or target_voice.voice_id
                    await self.repair_agent.repair_single_chunk(
                        chunk=target_chunk,
                        voice_id=v_to_use,
                        failure_reason=reason
                    )
                    self._save_chunk_to_db(project_id, target_chunk)

            qc_report = self.qc_agent.run_full_qc(chunks)
            state.qc_report = qc_report
            self.db.save_qc_report(project_id, qc_report.dict())

        # STEP 8: Timing, Subtitles & Timeline Alignment
        state.status = "SUBTITLE_GENERATING"
        state.progress_percentage = 85
        state.current_step_description = "Preparing subtitles & timestamps..."
        if progress_callback:
            await progress_callback(state)

        chunks = self.timing_agent.compute_timeline(chunks)
        state.chunks = chunks
        for c in chunks:
            self._save_chunk_to_db(project_id, c)

        srt_content = self.timing_agent.generate_srt(chunks)
        vtt_content = self.timing_agent.generate_vtt(chunks)
        total_duration = chunks[-1].end_time if chunks else 0.0
        timings_json_str = self.timing_agent.generate_timings_json(chunks, total_duration)

        srt_file = os.path.join(paths["subtitles"], "final.srt")
        vtt_file = os.path.join(paths["subtitles"], "final.vtt")
        json_file = os.path.join(paths["subtitles"], "timings.json")

        with open(srt_file, "w", encoding="utf-8") as f:
            f.write(srt_content)
        with open(vtt_file, "w", encoding="utf-8") as f:
            f.write(vtt_content)
        with open(json_file, "w", encoding="utf-8") as f:
            f.write(timings_json_str)

        state.final_srt = srt_file
        state.final_vtt = vtt_file
        state.final_timings_json = json_file
        state.total_duration_seconds = total_duration

        # STEP 9: Audio Assembly & Mastering Engine
        state.status = "MASTERING"
        state.progress_percentage = 92
        state.current_step_description = "Assembling audio & mastering (-14 LUFS)..."
        if progress_callback:
            await progress_callback(state)

        valid_files = [c.audio_file for c in chunks if c.audio_file and os.path.exists(c.audio_file)]
        pauses = [c.pause_after_ms for c in chunks]

        raw_master = os.path.join(paths["processed"], "assembled.wav")
        final_wav = os.path.join(paths["final"], "final.wav")
        final_mp3 = os.path.join(paths["final"], "final.mp3")

        self.audio_processor.concatenate_chunks_with_pauses(valid_files, pauses, raw_master)

        if os.path.exists(raw_master):
            if request.enable_audio_mastering:
                self.audio_processor.master_and_normalize_audio(raw_master, final_wav)
            else:
                import shutil
                shutil.copy(raw_master, final_wav)
            
            self.audio_processor.convert_to_mp3(final_wav, final_mp3)
            state.final_audio_wav = final_wav
            state.final_audio_mp3 = final_mp3

        # STEP 10: Complete & Persist
        state.status = "COMPLETED"
        state.progress_percentage = 100
        state.current_step_description = "Ready ✓"
        self._sync_state_to_db(state)

        self.memory_agent.record_project_completion(
            project_id=project_id,
            title=state.title,
            voice_id=target_voice.voice_id,
            duration=state.total_duration_seconds,
            qc_pass=state.qc_report.overall_pass if state.qc_report else True
        )

        if progress_callback:
            await progress_callback(state)

        return state

    async def redo_single_chunk(self, request: RedoChunkRequest) -> ProjectState:
        """
        Module 27: Line-by-Line Studio Surgical Redo.
        Regenerates ONLY that single target chunk with specified voice, emotion, or speed,
        reassembles the master audio, updates timestamps, and runs QC verification.
        """
        proj_data = self.db.get_project(request.project_id)
        if not proj_data:
            raise ValueError(f"Project {request.project_id} not found.")

        chunks_data = proj_data.get("chunks", [])
        target_chunk_dict = next((c for c in chunks_data if c["chunk_index"] == request.chunk_index), None)
        if not target_chunk_dict:
            raise ValueError(f"Chunk {request.chunk_index} not found.")

        # Ensure compatibility between DB column names and ChunkPlan fields
        if "normalized_text" not in target_chunk_dict or not target_chunk_dict["normalized_text"]:
            target_chunk_dict["normalized_text"] = target_chunk_dict.get("spoken_text") or target_chunk_dict["text"]
        if "audio_file" not in target_chunk_dict or not target_chunk_dict["audio_file"]:
            target_chunk_dict["audio_file"] = target_chunk_dict.get("audio_path")
        if not target_chunk_dict.get("assigned_voice_id"):
            target_chunk_dict["assigned_voice_id"] = target_chunk_dict.get("voice_id")

        target_chunk = ChunkPlan(**target_chunk_dict)

        # Apply overrides
        if request.custom_pronunciation_override:
            for w, r in request.custom_pronunciation_override.items():
                self.pronunciation_agent.save_user_entry(w, r)
            target_chunk.spoken_text = self.pronunciation_agent.apply_pronunciations(
                target_chunk.text, request.custom_pronunciation_override
            )
            target_chunk.normalized_text = target_chunk.spoken_text

        if request.custom_voice_id:
            target_chunk.voice_id = request.custom_voice_id
            target_chunk.assigned_voice_id = request.custom_voice_id

        if request.custom_speed is not None:
            target_chunk.speed = request.custom_speed
            target_chunk.rate = f"{int((request.custom_speed - 1.0) * 100):+d}%"

        if request.custom_emotion:
            target_chunk.emotion = request.custom_emotion

        voice_id = target_chunk.voice_id or target_chunk.assigned_voice_id or proj_data.get("voice_id") or "en-US-ChristopherNeural"
        target_chunk.voice_id = voice_id
        target_chunk.assigned_voice_id = voice_id

        # Surgical repair of that single chunk
        await self.repair_agent.repair_single_chunk(
            chunk=target_chunk,
            voice_id=voice_id,
            failure_reason="User Line-by-Line Redo Request"
        )
        self._save_chunk_to_db(request.project_id, target_chunk)

        # Reload updated chunks from database preserving voices
        updated_proj = self.db.get_project(request.project_id)
        all_chunks = []
        for c in updated_proj.get("chunks", []):
            if "normalized_text" not in c or not c["normalized_text"]:
                c["normalized_text"] = c.get("spoken_text") or c["text"]
            if "audio_file" not in c or not c["audio_file"]:
                c["audio_file"] = c.get("audio_path")
            if not c.get("assigned_voice_id"):
                c["assigned_voice_id"] = c.get("voice_id")
            if not c.get("voice_id"):
                c["voice_id"] = c.get("assigned_voice_id")
            all_chunks.append(ChunkPlan(**c))

        # Recalculate downstream timestamps
        all_chunks = self.timing_agent.compute_timeline(all_chunks)
        for c in all_chunks:
            self._save_chunk_to_db(request.project_id, c)

        # Reassemble audio & remaster
        paths = self._setup_project_storage(request.project_id)
        raw_master = os.path.join(paths["processed"], "assembled.wav")
        final_wav = os.path.join(paths["final"], "final.wav")
        final_mp3 = os.path.join(paths["final"], "final.mp3")

        valid_files = [c.audio_file for c in all_chunks if c.audio_file and os.path.exists(c.audio_file)]
        pauses = [c.pause_after_ms for c in all_chunks]

        self.audio_processor.concatenate_chunks_with_pauses(valid_files, pauses, raw_master)
        if os.path.exists(raw_master):
            self.audio_processor.master_and_normalize_audio(raw_master, final_wav)
            self.audio_processor.convert_to_mp3(final_wav, final_mp3)

        # Update subtitles
        srt_content = self.timing_agent.generate_srt(all_chunks)
        vtt_content = self.timing_agent.generate_vtt(all_chunks)
        total_duration = all_chunks[-1].end_time if all_chunks else 0.0
        timings_json_str = self.timing_agent.generate_timings_json(all_chunks, total_duration)

        with open(os.path.join(paths["subtitles"], "final.srt"), "w", encoding="utf-8") as f:
            f.write(srt_content)
        with open(os.path.join(paths["subtitles"], "final.vtt"), "w", encoding="utf-8") as f:
            f.write(vtt_content)
        with open(os.path.join(paths["subtitles"], "timings.json"), "w", encoding="utf-8") as f:
            f.write(timings_json_str)

        # Run QC on all chunks and save report (Step 2 item 11)
        qc_report = self.qc_agent.run_full_qc(all_chunks)
        self.db.save_qc_report(request.project_id, qc_report.dict())

        # Return updated project state
        refreshed = self.db.get_project(request.project_id)
        refreshed_chunks = []
        for c in refreshed.get("chunks", []):
            if "normalized_text" not in c or not c["normalized_text"]:
                c["normalized_text"] = c.get("spoken_text") or c["text"]
            if "audio_file" not in c or not c["audio_file"]:
                c["audio_file"] = c.get("audio_path")
            refreshed_chunks.append(ChunkPlan(**c))
        vp = find_voice_by_id_or_profile(refreshed.get("voice_id", ""))
        
        return ProjectState(
            project_id=refreshed["id"],
            title=refreshed["title"],
            raw_input=refreshed["raw_input"],
            detected_language=refreshed["language"],
            voice_profile=vp,
            status=refreshed["status"],
            progress_percentage=100,
            current_step_description="Line repaired successfully ✓",
            chunks=refreshed_chunks,
            final_audio_wav=refreshed["final_audio_wav"],
            final_audio_mp3=refreshed["final_audio_mp3"],
            final_srt=refreshed["final_srt"],
            final_vtt=refreshed["final_vtt"],
            final_timings_json=refreshed["final_timings_json"],
            total_duration_seconds=total_duration,
            qc_report=qc_report
        )

    def _sync_state_to_db(self, state: ProjectState):
        proj_dict = {
            "id": state.project_id,
            "title": state.title,
            "raw_input": state.raw_input,
            "original_text": state.original_text or state.raw_input,
            "normalized_text": state.chunks[0].normalized_text if state.chunks else "",
            "spoken_text": " ".join([c.spoken_text or c.normalized_text for c in state.chunks]) if state.chunks else "",
            "input_type": state.input_mode,
            "language": state.detected_language,
            "voice_id": state.voice_profile.voice_id if state.voice_profile else "",
            "voice_name": state.voice_profile.name if state.voice_profile else "",
            "style": state.voice_profile.style if state.voice_profile else "Cinematic",
            "emotion": state.emotion_mode,
            "status": state.status,
            "progress_percentage": state.progress_percentage,
            "current_step_description": state.current_step_description,
            "total_duration_seconds": state.total_duration_seconds,
            "final_audio_mp3": state.final_audio_mp3,
            "final_audio_wav": state.final_audio_wav,
            "final_srt": state.final_srt,
            "final_vtt": state.final_vtt,
            "final_timings_json": state.final_timings_json,
            "error_message": None
        }
        self.db.save_project(proj_dict)

    def _save_chunk_to_db(self, project_id: str, chunk: ChunkPlan):
        cd = {
            "project_id": project_id,
            "chunk_index": chunk.chunk_index,
            "speaker": chunk.speaker or chunk.speaker_name,
            "speaker_name": chunk.speaker_name or chunk.speaker,
            "character_id": chunk.character_id,
            "text": chunk.text,
            "spoken_text": chunk.spoken_text or chunk.normalized_text,
            "voice_id": chunk.voice_id or chunk.assigned_voice_id or "",
            "provider": chunk.provider or "edge-tts",
            "scene_id": chunk.scene_id,
            "emotion": chunk.emotion,
            "speed": chunk.speed,
            "pitch": chunk.pitch,
            "rate": chunk.rate,
            "pause_before_ms": chunk.pause_before_ms,
            "pause_after_ms": chunk.pause_after_ms,
            "audio_path": chunk.audio_file or chunk.audio_path,
            "duration": chunk.duration,
            "start_time": chunk.start_time,
            "end_time": chunk.end_time,
            "qc_status": "PASSED" if chunk.qc_pass else "FAILED",
            "qc_message": chunk.qc_message,
            "retry_count": chunk.attempt_count
        }
        self.db.save_chunk(cd)

    async def replace_character_voice(self, project_id: str, character_id: str, new_voice_id: str) -> Dict[str, Any]:
        """
        Replaces the voiceover for an entire character across all their dialogue lines,
        re-synthesizes those chunks, and remasters the final audio.
        """
        self.db.update_character_voice(project_id, character_id, new_voice_id)
        
        proj = self.db.get_project(project_id)
        if not proj:
            raise ValueError(f"Project {project_id} not found")
            
        chunks_data = proj.get("chunks", [])
        if not chunks_data:
            raise ValueError(f"No chunks found for project {project_id}")

        char_key = character_id.strip().lower()
        
        all_chunks: List[ChunkPlan] = []
        chunks_to_resynthesize: List[ChunkPlan] = []

        for c in chunks_data:
            if "normalized_text" not in c or not c["normalized_text"]:
                c["normalized_text"] = c.get("spoken_text") or c["text"]
            if "audio_file" not in c or not c["audio_file"]:
                c["audio_file"] = c.get("audio_path")
            if not c.get("assigned_voice_id"):
                c["assigned_voice_id"] = c.get("voice_id")
            if not c.get("voice_id"):
                c["voice_id"] = c.get("assigned_voice_id")
            
            cp = ChunkPlan(**c)
            spk = (cp.speaker_name or cp.speaker or cp.character_id or "").strip().lower()
            
            if spk == char_key or (cp.character_id and cp.character_id.strip().lower() == char_key):
                cp.voice_id = new_voice_id
                cp.assigned_voice_id = new_voice_id
                chunks_to_resynthesize.append(cp)
            
            all_chunks.append(cp)

        # Re-synthesize chunks for this character
        for target_chunk in chunks_to_resynthesize:
            await self.repair_agent.repair_single_chunk(
                chunk=target_chunk,
                voice_id=new_voice_id,
                failure_reason="User Character Voiceover Replacement"
            )
            self._save_chunk_to_db(project_id, target_chunk)

        # Recompute timeline
        all_chunks = self.timing_agent.compute_timeline(all_chunks)
        for c in all_chunks:
            self._save_chunk_to_db(project_id, c)

        # Concatenate & remaster
        paths = self._setup_project_storage(project_id)
        raw_master = os.path.join(paths["processed"], "assembled.wav")
        final_wav = os.path.join(paths["final"], "final.wav")
        final_mp3 = os.path.join(paths["final"], "final.mp3")

        valid_files = [c.audio_file for c in all_chunks if c.audio_file and os.path.exists(c.audio_file)]
        pauses = [c.pause_after_ms for c in all_chunks]

        self.audio_processor.concatenate_chunks_with_pauses(valid_files, pauses, raw_master)
        if os.path.exists(raw_master):
            self.audio_processor.master_and_normalize_audio(raw_master, final_wav)
            self.audio_processor.convert_to_mp3(final_wav, final_mp3)

        # Update subtitles
        srt_content = self.timing_agent.generate_srt(all_chunks)
        vtt_content = self.timing_agent.generate_vtt(all_chunks)
        total_duration = all_chunks[-1].end_time if all_chunks else 0.0
        timings_json_str = self.timing_agent.generate_timings_json(all_chunks, total_duration)

        with open(os.path.join(paths["subtitles"], "final.srt"), "w", encoding="utf-8") as f:
            f.write(srt_content)
        with open(os.path.join(paths["subtitles"], "final.vtt"), "w", encoding="utf-8") as f:
            f.write(vtt_content)
        with open(os.path.join(paths["subtitles"], "timings.json"), "w", encoding="utf-8") as f:
            f.write(timings_json_str)

        # Run QC
        qc_report = self.qc_agent.run_full_qc(all_chunks)
        self.db.save_qc_report(project_id, qc_report.dict())

        # Update project record
        self.db.update_project_status(
            project_id=project_id,
            status="COMPLETED",
            progress=100,
            description=f"Voiceover for character '{character_id}' replaced with {new_voice_id} ✓"
        )
        with self.db._get_connection() as conn:
            conn.cursor().execute("UPDATE projects SET total_duration_seconds = ? WHERE id = ?", (total_duration, project_id))
            conn.commit()

        return self.db.get_project(project_id)

    async def replace_project_voice(self, project_id: str, new_voice_id: str) -> Dict[str, Any]:
        """
        Replaces the main voiceover for the entire narration/project,
        re-synthesizes all chunks, and remasters the final audio.
        """
        proj = self.db.get_project(project_id)
        if not proj:
            raise ValueError(f"Project {project_id} not found")

        chunks_data = proj.get("chunks", [])
        if not chunks_data:
            raise ValueError(f"No chunks found for project {project_id}")

        all_chunks: List[ChunkPlan] = []
        for c in chunks_data:
            if "normalized_text" not in c or not c["normalized_text"]:
                c["normalized_text"] = c.get("spoken_text") or c["text"]
            if "audio_file" not in c or not c["audio_file"]:
                c["audio_file"] = c.get("audio_path")
            c["voice_id"] = new_voice_id
            c["assigned_voice_id"] = new_voice_id
            cp = ChunkPlan(**c)
            all_chunks.append(cp)

        # Re-synthesize all chunks
        for target_chunk in all_chunks:
            await self.repair_agent.repair_single_chunk(
                chunk=target_chunk,
                voice_id=new_voice_id,
                failure_reason="User Project Voiceover Replacement"
            )
            self._save_chunk_to_db(project_id, target_chunk)

        # Recompute timeline
        all_chunks = self.timing_agent.compute_timeline(all_chunks)
        for c in all_chunks:
            self._save_chunk_to_db(project_id, c)

        # Concatenate & remaster
        paths = self._setup_project_storage(project_id)
        raw_master = os.path.join(paths["processed"], "assembled.wav")
        final_wav = os.path.join(paths["final"], "final.wav")
        final_mp3 = os.path.join(paths["final"], "final.mp3")

        valid_files = [c.audio_file for c in all_chunks if c.audio_file and os.path.exists(c.audio_file)]
        pauses = [c.pause_after_ms for c in all_chunks]

        self.audio_processor.concatenate_chunks_with_pauses(valid_files, pauses, raw_master)
        if os.path.exists(raw_master):
            self.audio_processor.master_and_normalize_audio(raw_master, final_wav)
            self.audio_processor.convert_to_mp3(final_wav, final_mp3)

        # Update subtitles
        srt_content = self.timing_agent.generate_srt(all_chunks)
        vtt_content = self.timing_agent.generate_vtt(all_chunks)
        total_duration = all_chunks[-1].end_time if all_chunks else 0.0
        timings_json_str = self.timing_agent.generate_timings_json(all_chunks, total_duration)

        with open(os.path.join(paths["subtitles"], "final.srt"), "w", encoding="utf-8") as f:
            f.write(srt_content)
        with open(os.path.join(paths["subtitles"], "final.vtt"), "w", encoding="utf-8") as f:
            f.write(vtt_content)
        with open(os.path.join(paths["subtitles"], "timings.json"), "w", encoding="utf-8") as f:
            f.write(timings_json_str)

        # Run QC
        qc_report = self.qc_agent.run_full_qc(all_chunks)
        self.db.save_qc_report(project_id, qc_report.dict())

        # Update project record
        vp = find_voice_by_id_or_profile(new_voice_id)
        vname = vp.name if vp else new_voice_id
        with self.db._get_connection() as conn:
            conn.cursor().execute("""
                UPDATE projects 
                SET voice_id = ?, voice_name = ?, total_duration_seconds = ?,
                    current_step_description = 'Voiceover replaced successfully ✓',
                    status = 'COMPLETED'
                WHERE id = ?
            """, (new_voice_id, vname, total_duration, project_id))
            conn.commit()

        return self.db.get_project(project_id)
