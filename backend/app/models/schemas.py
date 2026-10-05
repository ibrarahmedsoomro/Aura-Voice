from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator
from datetime import datetime

class PronunciationEntry(BaseModel):
    word: str
    replacement: str
    language: Optional[str] = "en"

class VoiceProfile(BaseModel):
    voice_id: str
    name: str
    gender: str  # "Male" | "Female"
    language: str  # "en", "ur", "hi", etc.
    locale: str   # "en-US", "ur-PK", "hi-IN", "en-GB"
    style: str    # "Cinematic", "Documentary", "Storyteller", "Horror", "Conversational", "News"
    provider: str # "edge-tts" | "gemini" | "elevenlabs" | "local"
    license_type: str = "LICENSED_PROVIDER"  # "LICENSED_PROVIDER", "USER_OWNED", "ORIGINAL_SYNTHETIC"
    description: str = ""
    is_authorized: bool = True
    qc_rating: float = 0.98

class ProjectCharacter(BaseModel):
    character_id: str
    speaker_name: str
    voice_id: str
    provider: str = "edge-tts"
    is_locked: bool = False
    style: str = "Cinematic"
    confidence: float = 0.95
    reason: str = ""

class ScenePlan(BaseModel):
    scene_id: str
    scene_index: int
    scene_name: str = ""
    location: str = ""
    time_of_day: str = ""
    mood: str = "neutral"
    dramatic_intensity: float = 0.5
    characters: List[str] = []

class ChunkPlan(BaseModel):
    chunk_index: int
    text: str
    normalized_text: str = ""
    spoken_text: Optional[str] = None
    character_id: Optional[str] = None
    speaker_name: Optional[str] = None
    speaker: Optional[str] = None
    voice_id: Optional[str] = None
    assigned_voice_id: Optional[str] = None
    provider: str = "edge-tts"
    scene_id: Optional[str] = None
    emotion: str = "neutral"
    emotion_intensity: float = 0.5
    dramatic_intensity: float = 0.5
    speed: float = 1.0       # e.g. 0.85 to 1.15
    pitch: str = "+0Hz"      # Edge-TTS format e.g. "+0Hz", "-5Hz"
    rate: str = "+0%"        # Edge-TTS format e.g. "-10%", "+5%"
    pause_before_ms: int = 150
    pause_after_ms: int = 400
    stress_words: List[str] = []
    
    # State & execution
    audio_file: Optional[str] = None
    audio_path: Optional[str] = None
    duration: float = 0.0
    start_time: float = 0.0
    end_time: float = 0.0
    qc_status: Optional[str] = None
    qc_pass: bool = False
    qc_message: Optional[str] = None
    attempt_count: int = 0

    @model_validator(mode="after")
    def sync_aliases(self):
        # Sync speaker aliases
        if not self.speaker and self.speaker_name:
            self.speaker = self.speaker_name
        if not self.speaker_name and self.speaker:
            self.speaker_name = self.speaker
            
        # Sync voice_id aliases
        effective_v = self.voice_id or self.assigned_voice_id
        if effective_v:
            self.voice_id = effective_v
            self.assigned_voice_id = effective_v

        # Sync audio aliases
        effective_audio = self.audio_file or self.audio_path
        if effective_audio:
            self.audio_file = effective_audio
            self.audio_path = effective_audio

        # Sync spoken text
        if not self.spoken_text and self.normalized_text:
            self.spoken_text = self.normalized_text
        if not self.normalized_text and self.spoken_text:
            self.normalized_text = self.spoken_text
            
        return self

class QCResult(BaseModel):
    overall_pass: bool
    text_accuracy_score: float = 1.0
    audio_integrity_score: float = 1.0
    detected_clipping: bool = False
    detected_unnatural_silence: bool = False
    failed_chunk_indices: List[int] = []
    repair_suggestions: Dict[int, str] = {}
    details: Dict[str, Any] = {}

class ProjectState(BaseModel):
    project_id: str
    title: str = "Untitled Project"
    raw_input: str
    original_text: Optional[str] = None
    input_mode: str = "text" # "text" | "topic" | "file"
    detected_language: str = "en"
    voice_profile: Optional[VoiceProfile] = None
    emotion_mode: str = "auto"
    status: str = "IDLE"  # IDLE, UNDERSTANDING, PLANNING, GENERATING, QC_ANALYSIS, REPAIRING, COMPLETED, FAILED
    progress_percentage: int = 0
    current_step_description: str = ""
    characters: List[ProjectCharacter] = []
    scenes: List[ScenePlan] = []
    chunks: List[ChunkPlan] = []
    qc_report: Optional[QCResult] = None
    
    # Final Output files
    final_audio_wav: Optional[str] = None
    final_audio_mp3: Optional[str] = None
    final_srt: Optional[str] = None
    final_vtt: Optional[str] = None
    final_timings_json: Optional[str] = None
    total_duration_seconds: float = 0.0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class GenerateVoiceRequest(BaseModel):
    text: str
    topic_prompt: Optional[str] = None
    voice_id: Optional[str] = "auto"
    style_preference: Optional[str] = "Cinematic" # "Cinematic", "Documentary", "Storyteller", "Horror", "Conversational"
    emotion_mode: Optional[str] = "auto" # "auto", "suspense", "dramatic", "calm", "energetic", "horror"
    language_hint: Optional[str] = "auto" # "auto", "en", "ur", "hi", "roman_urdu"
    custom_pronunciations: Optional[Dict[str, str]] = None
    character_overrides: Optional[Dict[str, str]] = None # {"Commander": "en-US-BrianMultilingualNeural"}
    locked_characters: Optional[List[str]] = None
    enable_audio_mastering: bool = True
    background_sfx: Optional[str] = None # None, "rain_ambient", "cinematic_drone", "lofi_pad"

class RedoChunkRequest(BaseModel):
    project_id: str
    chunk_index: int
    custom_voice_id: Optional[str] = None
    custom_pronunciation_override: Optional[Dict[str, str]] = None
    custom_speed: Optional[float] = None
    custom_emotion: Optional[str] = None
