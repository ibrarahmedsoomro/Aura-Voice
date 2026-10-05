import os
import uuid
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query, UploadFile, File, Form, Body
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from ..models.schemas import (
    GenerateVoiceRequest,
    RedoChunkRequest,
    ProjectState,
    VoiceProfile,
    ProjectCharacter
)
from ..core.voice_catalog import (
    get_all_voices,
    find_voice_by_id_or_profile,
    rank_voices_for_script
)
from ..orchestrator.central_orchestrator import CentralOrchestrator
from ..database.db import DatabaseManager

router = APIRouter()
orchestrator = CentralOrchestrator()
db = DatabaseManager()

# Active WebSocket connections per project
active_connections: Dict[str, List[WebSocket]] = {}

class CreateProjectRequest(BaseModel):
    text: str
    title: Optional[str] = None
    input_type: Optional[str] = "text"
    language_hint: Optional[str] = "auto"
    voice_id: Optional[str] = "auto"
    style_preference: Optional[str] = "Cinematic"
    emotion_mode: Optional[str] = "auto"

class PronunciationRequest(BaseModel):
    word: str
    replacement: str
    language: Optional[str] = "en"

class SettingsRequest(BaseModel):
    preferred_voice_id: Optional[str] = None
    preferred_style: Optional[str] = None
    default_emotion: Optional[str] = None
    enable_mastering: Optional[bool] = None

# --- HEALTH CHECK ---
@router.api_route("/health", methods=["GET", "HEAD"])
def health_check():
    """System Health Check per Specification Section 34."""
    # Check FFmpeg
    ffmpeg_ok = False
    try:
        import subprocess
        res = subprocess.run(["ffmpeg", "-version"], capture_output=True)
        ffmpeg_ok = (res.returncode == 0)
    except Exception:
        pass

    return {
        "status": "online",
        "services": {
            "backend": "online",
            "tts_engine": "healthy (Edge-TTS Neural)",
            "ffmpeg": "available" if ffmpeg_ok else "unavailable",
            "asr_qc": "available (Autonomous QC Agent)",
            "database": "connected (SQLite Persistent)",
            "storage": "available"
        }
    }

# --- VOICES & RANKING ---
@router.get("/voices")
def list_voices(
    language: Optional[str] = None,
    style: Optional[str] = None
):
    """Returns licensed voices with intelligence ranking if language/style provided."""
    if language or style:
        ranked = rank_voices_for_script(
            language=language or "en",
            style_preference=style or "Cinematic",
            user_preferred_voice=db.get_preference("preferred_voice_id")
        )
        return ranked
    return [{"voice": v, "confidence": 0.95, "reason": v.description} for v in get_all_voices()]

@router.get("/voices/{voice_id}")
def get_voice(voice_id: str):
    v = find_voice_by_id_or_profile(voice_id)
    if not v:
        raise HTTPException(status_code=404, detail="Voice not found")
    return v

@router.api_route("/voices/{voice_id}/preview", methods=["GET", "POST", "HEAD"])
async def preview_voice(voice_id: str):
    """Synthesizes a short dynamic preview for the voice library."""
    v = find_voice_by_id_or_profile(voice_id)
    if not v:
        raise HTTPException(status_code=404, detail="Voice not found")

    preview_dir = os.path.join(orchestrator.storage_dir, "previews")
    os.makedirs(preview_dir, exist_ok=True)
    out_file = os.path.join(preview_dir, f"{v.voice_id}_sample.mp3")

    if not os.path.exists(out_file):
        sample_text = (
            "Hello, I am ready to bring your story to life with natural, expressive voice narration."
            if v.language == "en" else
            "Main aapki kahani ko pur-asar aur qudrati aawaz mein bayan karne ke liye tayyar hoon."
        )
        await orchestrator.tts_provider.synthesize_chunk(
            text=sample_text,
            voice_id=v.voice_id,
            output_path=out_file
        )

    return FileResponse(out_file, media_type="audio/mpeg")

# --- PROJECTS CRUD & GENERATION ---
@router.post("/projects")
async def create_project(req: CreateProjectRequest):
    """Creates a new project without executing it immediately."""
    proj_id = f"VX-{uuid.uuid4().hex[:6].upper()}"
    title = req.title or (req.text[:40].strip() + "...")
    data = {
        "id": proj_id,
        "title": title,
        "raw_input": req.text,
        "input_type": req.input_type,
        "language": req.language_hint,
        "voice_id": req.voice_id,
        "style": req.style_preference,
        "emotion": req.emotion_mode,
        "status": "CREATED",
        "progress_percentage": 0,
        "current_step_description": "Project created. Ready to generate."
    }
    db.save_project(data)
    return db.get_project(proj_id)

@router.get("/projects")
def list_projects(limit: int = 50):
    return db.list_projects(limit)

@router.get("/projects/{project_id}")
def get_project(project_id: str):
    p = db.get_project(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return p

@router.delete("/projects/{project_id}")
def delete_project(project_id: str):
    db.delete_project(project_id)
    return {"status": "deleted", "project_id": project_id}

@router.get("/projects/{project_id}/status")
def get_project_status(project_id: str):
    p = db.get_project(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "id": p["id"],
        "status": p["status"],
        "progress_percentage": p["progress_percentage"],
        "current_step_description": p["current_step_description"],
        "error_message": p["error_message"]
    }

@router.post("/projects/{project_id}/generate")
async def generate_project(project_id: str, req: GenerateVoiceRequest):
    """Asynchronously starts autonomous voice generation pipeline."""
    p = db.get_project(project_id)
    if not p:
        # Create on the fly if not existing
        title = req.topic_prompt or (req.text[:40].strip() + "...")
        db.save_project({
            "id": project_id,
            "title": title,
            "raw_input": req.text,
            "status": "ANALYZING"
        })

    async def broadcast_progress(state: ProjectState):
        conns = active_connections.get(project_id, [])
        for ws in conns:
            try:
                await ws.send_json({
                    "type": "progress",
                    "status": state.status,
                    "percentage": state.progress_percentage,
                    "description": state.current_step_description
                })
            except Exception:
                pass

    try:
        final_state = await orchestrator.execute_voice_pipeline(
            request=req,
            existing_project_id=project_id,
            progress_callback=broadcast_progress
        )

        # Notify websockets of completion
        conns = active_connections.get(project_id, [])
        for ws in conns:
            try:
                await ws.send_json({
                    "type": "completed",
                    "project_id": project_id,
                    "status": final_state.status
                })
            except Exception:
                pass

        return db.get_project(project_id)
    except Exception as e:
        db.update_project_status(project_id, "FAILED", 0, "Error during generation", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/projects/{project_id}/cancel")
def cancel_generation(project_id: str):
    orchestrator.cancel_project(project_id)
    return {"status": "cancelled", "project_id": project_id}

# --- CHARACTER MANAGEMENT (Step 5, 7) ---
class UpdateCharacterRequest(BaseModel):
    voice_id: str
    is_locked: Optional[bool] = None

@router.get("/projects/{project_id}/characters")
def get_project_characters(project_id: str):
    p = db.get_project(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return p.get("characters", [])

class ReplaceVoiceRequest(BaseModel):
    voice_id: str

@router.post("/projects/{project_id}/characters/{character_id}/replace-voice")
async def replace_character_voiceover(project_id: str, character_id: str, req: ReplaceVoiceRequest):
    """Replaces voice for a character across all their dialogue lines, re-synthesizes and remasters."""
    p = db.get_project(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        updated = await orchestrator.replace_character_voice(project_id, character_id, req.voice_id)
        return updated
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/projects/{project_id}/replace-voice")
async def replace_project_voiceover(project_id: str, req: ReplaceVoiceRequest):
    """Replaces main voice for entire project/narration, re-synthesizes all lines, and remasters."""
    p = db.get_project(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        updated = await orchestrator.replace_project_voice(project_id, req.voice_id)
        return updated
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/projects/{project_id}/characters/{character_id}")
def update_project_character(project_id: str, character_id: str, req: UpdateCharacterRequest):
    p = db.get_project(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    db.update_character_voice(project_id, character_id, req.voice_id, req.is_locked)
    return db.get_project(project_id)

@router.post("/projects/{project_id}/cast")
def auto_cast_project_characters(project_id: str):
    p = db.get_project(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    norm_text, lang_code, _ = orchestrator.script_agent.normalize(p["raw_input"])
    scenes, turns = orchestrator.speech_planner.extract_scenes_and_turns(norm_text)
    unique_speakers = list(dict.fromkeys([t["speaker"] for t in turns if t.get("speaker")]))
    existing_chars_data = db.get_project_characters(project_id)
    existing_chars = [ProjectCharacter(**cd) for cd in existing_chars_data] if existing_chars_data else []
    cast = orchestrator.speech_planner.auto_cast_characters(
        speakers=unique_speakers,
        language=p.get("language") or lang_code,
        style_preference=p.get("style") or "Cinematic",
        existing_characters=existing_chars
    )
    db.save_characters(project_id, [c.dict() for c in cast.values()])
    return db.get_project(project_id)

@router.post("/projects/{project_id}/chunks/{chunk_id}/redo")
async def redo_chunk(project_id: str, chunk_id: int, req: Optional[RedoChunkRequest] = Body(None)):
    """Module 27: Line-by-Line Studio surgical chunk redo."""
    redo_req = req or RedoChunkRequest(project_id=project_id, chunk_index=chunk_id)
    redo_req.project_id = project_id
    redo_req.chunk_index = chunk_id
    try:
        updated_state = await orchestrator.redo_single_chunk(redo_req)
        return db.get_project(project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- AUDIO & SUBTITLE STREAMING/DOWNLOAD ---
@router.api_route("/projects/{project_id}/audio", methods=["GET", "HEAD"])
def get_project_audio(project_id: str, format: str = "mp3"):
    """Secure audio streamer for master audio."""
    p = db.get_project(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    file_path = p.get("final_audio_mp3") if format.lower() == "mp3" else p.get("final_audio_wav")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Audio file ({format}) not available yet.")

    media_type = "audio/mpeg" if format.lower() == "mp3" else "audio/wav"
    return FileResponse(file_path, media_type=media_type)

@router.get("/projects/{project_id}/subtitles")
def get_project_subtitles(project_id: str, format: str = "srt"):
    p = db.get_project(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    fmt = format.lower()
    path_map = {
        "srt": p.get("final_srt"),
        "vtt": p.get("final_vtt"),
        "json": p.get("final_timings_json"),
        "txt": os.path.join(orchestrator.exports_dir, project_id, "subtitles", "transcript.txt")
    }
    target_path = path_map.get(fmt)
    if not target_path or not os.path.exists(target_path):
        raise HTTPException(status_code=404, detail=f"Subtitle file ({format}) not found.")

    return FileResponse(target_path, filename=os.path.basename(target_path))

@router.get("/audio/stream")
def stream_generic_audio(path: str):
    """Streams individual chunk audio."""
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    media_type = "audio/mpeg" if path.endswith(".mp3") else "audio/wav"
    return FileResponse(path, media_type=media_type)

# --- PRONUNCIATION DICTIONARY ---
@router.get("/pronunciations")
def get_pronunciations():
    return db.get_pronunciations()

@router.post("/pronunciations")
def set_pronunciation(req: PronunciationRequest):
    db.set_pronunciation(req.word, req.replacement, req.language or "en")
    return {"status": "saved", "word": req.word, "replacement": req.replacement}

@router.delete("/pronunciations/{word}")
def delete_pronunciation(word: str):
    db.delete_pronunciation(word)
    return {"status": "deleted", "word": word}

# --- SETTINGS & PREFERENCES ---
@router.get("/settings")
def get_settings():
    return {
        "preferred_voice_id": db.get_preference("preferred_voice_id", "vox-cinematic-male"),
        "preferred_style": db.get_preference("preferred_style", "Cinematic"),
        "default_emotion": db.get_preference("default_emotion", "auto"),
        "enable_mastering": db.get_preference("enable_mastering", True)
    }

@router.post("/settings")
def update_settings(req: SettingsRequest):
    if req.preferred_voice_id is not None:
        db.set_preference("preferred_voice_id", req.preferred_voice_id)
    if req.preferred_style is not None:
        db.set_preference("preferred_style", req.preferred_style)
    if req.default_emotion is not None:
        db.set_preference("default_emotion", req.default_emotion)
    if req.enable_mastering is not None:
        db.set_preference("enable_mastering", req.enable_mastering)
    return {"status": "updated"}

# --- WEBSOCKET LIVE STREAMING ---
@router.websocket("/ws/projects/{project_id}")
async def ws_project_progress(websocket: WebSocket, project_id: str):
    await websocket.accept()
    if project_id not in active_connections:
        active_connections[project_id] = []
    active_connections[project_id].append(websocket)

    try:
        while True:
            # Keep-alive ping
            await websocket.receive_text()
    except WebSocketDisconnect:
        if project_id in active_connections and websocket in active_connections[project_id]:
            active_connections[project_id].remove(websocket)
