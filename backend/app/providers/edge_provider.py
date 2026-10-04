import os
import asyncio
import edge_tts
from typing import Dict, Any
from .base import BaseTTSProvider

class EdgeTTSProvider(BaseTTSProvider):
    """
    High-fidelity neural voice provider using Edge TTS.
    Zero API key required, supports multilingual neural voices with pitch & rate modulation.
    """

    async def synthesize_chunk(
        self,
        text: str,
        voice_id: str,
        rate: str = "+0%",
        pitch: str = "+0Hz",
        output_path: str = ""
    ) -> Dict[str, Any]:
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Format pitch and rate safely
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice_id,
                rate=rate,
                pitch=pitch
            )
            
            await communicate.save(output_path)
            
            # Check if file exists and has size
            if os.path.exists(output_path) and os.path.getsize(output_path) > 100:
                return {
                    "success": True,
                    "output_path": output_path,
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "output_path": None,
                    "error": "Generated audio file is empty or missing"
                }
        except Exception as e:
            return {
                "success": False,
                "output_path": None,
                "error": str(e)
            }
