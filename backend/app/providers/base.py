from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseTTSProvider(ABC):
    """Abstract interface for all TTS engines (EdgeTTS, ElevenLabs, Gemini, Local)"""
    
    @abstractmethod
    async def synthesize_chunk(
        self,
        text: str,
        voice_id: str,
        rate: str,
        pitch: str,
        output_path: str
    ) -> Dict[str, Any]:
        """
        Synthesizes text to output_path.
        Returns metadata: {"duration": float, "success": bool, "error": Optional[str]}
        """
        pass
