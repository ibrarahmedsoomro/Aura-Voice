import os
import uuid
import asyncio
import json
from typing import Callable, Optional, Dict, Any, List
from datetime import datetime

from ..models.schemas import (
    ProjectState,
    GenerateVoiceRequest,
    ChunkPlan,
    QCResult,
    RedoChunkRequest
)
from ..core.voice_catalog import (
    resolve_voice_recommendation,
    find_voice_by_id_or_profile,
    verify_voice_consent_and_policy,
    rank_voices_for_script,
    VOICE_CATALOG
)
from ..database.db import DatabaseManager
from ..agents.script_intelligence import ScriptIntelligenceAgent
from ..agents.emotion_performance import EmotionPerformanceAgent
from ..agents.pronunciation import PronunciationAgent
from ..agents.speech_planner import SpeechPlannerAgent
from ..agents.audio_processor import AudioProcessorAgent
from ..agents.timing_alignment import TimingAlignmentAgent
from ..agents.qc_agent import AutonomousQCAgent
from ..agents.repair_agent import AutonomousRepairAgent
from ..agents.memory_agent import ProjectMemoryAgent
from ..providers.edge_provider import EdgeTTSProvider

class CentralOrchestrator:
    """
    Module 21 & 22: Central Stateful Orchestrator
    Autonomous loop: Understand → Plan → Select Voice → Synthesize → QC → Repair → Master → Subtitles → Deliver
    Persists all state to SQLite and structured file storage.
    """

    def __init__(self, storage_dir: Optional[str] = None, exports_dir: Optional[str] = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.storage_dir = storage_dir or os.path.join(base_dir, "storage")
        self.exports_dir = exports_dir or os.path.join(base_dir, "exports")
        os.makedirs(self.storage_dir, exist_ok=True)
        os.makedirs(self.exports_dir, exist_ok=True)

        # Database Manager
        self.db = DatabaseManager()

        # Agents
        self.script_agent = ScriptIntelligenceAgent()
        self.emotion_agent = EmotionPerformanceAgent()
        self.pronunciation_agent = PronunciationAgent(self.db)
        self.speech_planner = SpeechPlannerAgent(self.emotion_agent, self.pronunciation_agent)
        self.audio_processor = AudioProcessorAgent()
        self.timing_agent = TimingAlignmentAgent()
        self.qc_agent = AutonomousQCAgent()
        self.tts_provider = EdgeTTSProvider()
        self.repair_agent = AutonomousRepairAgent(self.tts_provider, self.audio_processor, self.qc_agent)
        self.memory_agent = ProjectMemoryAgent(os.path.join(self.storage_dir, "memory"))

        # In-flight cancellations tracking
        self.cancelled_projects: set = set()

    def _setup_project_storage(self, project_id: str) -> Dict[str, str]:
        """Creates structured folders per Specification Section 37."""
        proj_root = os.path.join(self.exports_dir, project_id)
        dirs = {
            "root": proj_root,
            "raw": os.path.join(proj_root, "raw"),
            "processed": os.path.join(proj_root, "processed"),
            "final": os.path.join(proj_root, "final"),
            "subtitles": os.path.join(proj_root, "subtitles"),
            "metadata": os.path.join(proj_root, "metadata")
        }
        for d in dirs.values():
            os.makedirs(d, exist_ok=True)
        return dirs

    def cancel_project(self, project_id: str):
        self.cancelled_projects.add(project_id)
        self.db.update_project_status(project_id, "CANCELLED", 0, "Generation was cancelled by user.")

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

        # Initialize Project State
        state = ProjectState(
            project_id=project_id,
            title=request.topic_prompt or (request.text[:40].strip() + "..."),
            raw_input=request.text,
            status="ANALYZING",
            progress_percentage=10,
            current_step_description="Analyzing your script..."
        )
        self._sync_state_to_db(state)
        if progress_callback:
            await progress_callback(state)

        # STEP 1: Script Intelligence
        norm_text, lang_code, lang_desc = self.script_agent.normalize(request.text)
        state.detected_language = lang_code
        state.progress_percentage = 20
        state.current_step_description = f"Detected language: {lang_desc} ✓"
        self._sync_state_to_db(state)
        if progress_callback:
            await progress_callback(state)

        if project_id in self.cancelled_projects:
            state.status = "CANCELLED"
            return state

        # STEP 2: Voice Intelligence & Policy Check
        state.status = "VOICE_SELECTING"
        state.progress_percentage = 30
        state.current_step_description = "Selecting the best voice profile ✓"
        
        target_voice = None
        if request.voice_id and request.voice_id != "auto":
            safety_check = verify_voice_consent_and_policy(request.voice_id)
            if not safety_check["allowed"]:
                target_voice = safety_check["substitute_profile"]
            else:
                target_voice = find_voice_by_id_or_profile(request.voice_id)

        if not target_voice:
            user_pref = self.db.get_preference("preferred_voice_id")
            target_voice = resolve_voice_recommendation(
                language=lang_code,
                style_pref=request.style_preference or "Cinematic"
            )

        state.voice_profile = target_voice
        self._sync_state_to_db(state)
        if progress_callback:
            await progress_callback(state)

        # STEP 3: Speech Planning & Pronunciation
        state.status = "SPEECH_PLANNING"
        state.progress_percentage = 40
        state.current_step_description = "Planning narration & breath pacing ✓"
        
        chunks = self.speech_planner.plan_speech(
            normalized_text=norm_text,
            emotion_mode=request.emotion_mode or "auto",
            custom_pronunciations=request.custom_pronunciations
        )
        state.chunks = chunks
        self._sync_state_to_db(state)
        if progress_callback:
            await progress_callback(state)

        # STEP 4: Parallel Speech Synthesis
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

            res = await self.tts_provider.synthesize_chunk(
                text=chunk.normalized_text,
                voice_id=target_voice.voice_id,
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

            # Persist chunk
            self._save_chunk_to_db(project_id, chunk)

            pct = 40 + int(((i + 1) / total_chunks) * 30)
            state.progress_percentage = min(70, pct)
            state.current_step_description = f"Generating voice... {i + 1} / {total_chunks} chunks"
            if progress_callback:
                await progress_callback(state)

        # STEP 5: Quality Control Check
        state.status = "QC_RUNNING"
        state.progress_percentage = 75
        state.current_step_description = "Running quality check..."
        if progress_callback:
            await progress_callback(state)

        qc_report = self.qc_agent.run_full_qc(chunks)
        state.qc_report = qc_report

        # STEP 6: Targeted Surgical Repair Loop (if any chunk failed)
        if not qc_report.overall_pass and qc_report.failed_chunk_indices:
            state.status = "REPAIRING"
            state.current_step_description = f"Repairing {len(qc_report.failed_chunk_indices)} line(s)..."
            if progress_callback:
                await progress_callback(state)

            for failed_idx in qc_report.failed_chunk_indices:
                target_chunk = next((c for c in chunks if c.chunk_index == failed_idx), None)
                if target_chunk:
                    reason = qc_report.repair_suggestions.get(failed_idx, "Cadence anomaly")
                    await self.repair_agent.repair_single_chunk(
                        chunk=target_chunk,
                        voice_id=target_voice.voice_id,
                        failure_reason=reason
                    )
                    self._save_chunk_to_db(project_id, target_chunk)

            qc_report = self.qc_agent.run_full_qc(chunks)
            state.qc_report = qc_report

        # STEP 7: Timing & Subtitles Engine
        state.status = "SUBTITLE_GENERATING"
        state.progress_percentage = 85
        state.current_step_description = "Preparing subtitles & timestamps..."
        if progress_callback:
            await progress_callback(state)

        chunks = self.timing_agent.compute_timeline(chunks)
        state.chunks = chunks

        srt_content = self.timing_agent.generate_srt(chunks)
        vtt_content = self.timing_agent.generate_vtt(chunks)
        total_duration = chunks[-1].end_time if chunks else 0.0
        timings_json_str = self.timing_agent.generate_timings_json(chunks, total_duration)

        srt_path = os.path.join(paths["subtitles"], "final.srt")
        vtt_path = os.path.join(paths["subtitles"], "final.vtt")
        json_path = os.path.join(paths["subtitles"], "timings.json")
        txt_path = os.path.join(paths["subtitles"], "transcript.txt")

        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(srt_content)
        with open(vtt_path, "w", encoding="utf-8") as f:
            f.write(vtt_content)
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(timings_json_str)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(norm_text)

        state.final_srt = srt_path
        state.final_vtt = vtt_path
        state.final_timings_json = json_path
        state.total_duration_seconds = total_duration

        # STEP 8: Mastering Audio
        state.status = "POST_PROCESSING"
        state.progress_percentage = 92
        state.current_step_description = "Final mastering..."
        if progress_callback:
            await progress_callback(state)

        raw_master = os.path.join(paths["processed"], "assembled.wav")
        final_wav = os.path.join(paths["final"], "final.wav")
        final_mp3 = os.path.join(paths["final"], "final.mp3")

        valid_files = [c.audio_file for c in chunks if c.audio_file and os.path.exists(c.audio_file)]
        pauses = [c.pause_after_ms for c in chunks]

        concat_ok = self.audio_processor.concatenate_chunks_with_pauses(valid_files, pauses, raw_master)
        if concat_ok and os.path.exists(raw_master):
            if request.enable_audio_mastering:
                self.audio_processor.master_and_normalize_audio(raw_master, final_wav)
            else:
                import shutil
                shutil.copy(raw_master, final_wav)
            
            self.audio_processor.convert_to_mp3(final_wav, final_mp3)
            state.final_audio_wav = final_wav
            state.final_audio_mp3 = final_mp3

        # STEP 9: Complete & Persist
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
        """Module 27: Line-by-Line Studio Redo - Surgically regenerates ONE chunk."""
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

        target_chunk = ChunkPlan(**target_chunk_dict)

        # Apply overrides
        if request.custom_pronunciation_override:
            for w, r in request.custom_pronunciation_override.items():
                self.pronunciation_agent.save_user_entry(w, r)
            target_chunk.normalized_text = self.pronunciation_agent.apply_pronunciations(
                target_chunk.text, request.custom_pronunciation_override
            )

        if request.custom_speed:
            speed_pct = int((request.custom_speed - 1.0) * 100)
            target_chunk.rate = f"{'+' if speed_pct >= 0 else ''}{speed_pct}%"

        voice_id = proj_data.get("voice_id") or "en-US-ChristopherNeural"

        # Surgical repair of that single chunk
        await self.repair_agent.repair_single_chunk(
            chunk=target_chunk,
            voice_id=voice_id,
            failure_reason="User Line-by-Line Redo Request"
        )
        self._save_chunk_to_db(request.project_id, target_chunk)

        # Reload updated chunks from database
        updated_proj = self.db.get_project(request.project_id)
        all_chunks = []
        for c in updated_proj.get("chunks", []):
            if "normalized_text" not in c or not c["normalized_text"]:
                c["normalized_text"] = c.get("spoken_text") or c["text"]
            if "audio_file" not in c or not c["audio_file"]:
                c["audio_file"] = c.get("audio_path")
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
            total_duration_seconds=total_duration
        )

    def _sync_state_to_db(self, state: ProjectState):
        proj_dict = {
            "id": state.project_id,
            "title": state.title,
            "raw_input": state.raw_input,
            "original_text": state.raw_input,
            "normalized_text": state.chunks[0].normalized_text if state.chunks else "",
            "spoken_text": " ".join([c.normalized_text for c in state.chunks]) if state.chunks else "",
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
            "text": chunk.text,
            "spoken_text": chunk.normalized_text,
            "voice_id": "",
            "emotion": chunk.emotion,
            "speed": chunk.speed,
            "pitch": chunk.pitch,
            "rate": chunk.rate,
            "pause_before_ms": chunk.pause_before_ms,
            "pause_after_ms": chunk.pause_after_ms,
            "audio_path": chunk.audio_file,
            "duration": chunk.duration,
            "start_time": chunk.start_time,
            "end_time": chunk.end_time,
            "qc_status": "PASSED" if chunk.qc_pass else "FAILED",
            "qc_message": chunk.qc_message,
            "retry_count": chunk.attempt_count
        }
        self.db.save_chunk(cd)
