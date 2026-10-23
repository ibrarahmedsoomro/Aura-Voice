from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseTTSProvider(ABC):
    """Abstract interface for all TTS engines (EdgeTTS, LocalMMS, etc.)"""
    
    @property
    def provider_id(self) -> str:
        """Unique identifier of the provider (e.g. 'edge-tts', 'local-mms')"""
        return "base"

    @property
    def is_local(self) -> bool:
        """Whether this provider runs offline locally on the machine without network calls"""
        return False

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
        Returns metadata: {"duration": float, "success": bool, "cached": bool, "error": Optional[str]}
        """
        pass
