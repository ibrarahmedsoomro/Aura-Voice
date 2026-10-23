import os
import shutil
import hashlib
import asyncio
from typing import Dict, Any
import edge_tts
from .base import BaseTTSProvider

class EdgeTTSProvider(BaseTTSProvider):
    """
    High-fidelity neural voice provider using Edge TTS.
    Zero API key required, supports multilingual neural voices with pitch & rate modulation.
    Enhanced with intelligent persistent caching and parallel connection resilience.
    """

    def __init__(self, cache_dir: str = None):
        if cache_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            cache_dir = os.path.join(base_dir, "storage", "cache", "tts_chunks")
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    @property
    def provider_id(self) -> str:
        return "edge-tts"

    @property
    def is_local(self) -> bool:
        return False

    def _get_cache_path(self, text: str, voice_id: str, rate: str, pitch: str) -> str:
        cache_key = hashlib.sha256(f"{voice_id}|{rate}|{pitch}|{text}".encode("utf-8")).hexdigest()
        return os.path.join(self.cache_dir, f"{cache_key}.mp3")

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
            cache_file = self._get_cache_path(text, voice_id, rate, pitch)

            # Check persistent cache
            if os.path.exists(cache_file) and os.path.getsize(cache_file) > 100:
                try:
                    shutil.copyfile(cache_file, output_path)
                    return {
                        "success": True,
                        "output_path": output_path,
                        "cached": True,
                        "error": None
                    }
                except Exception:
                    pass

            # Retry loop for resilient parallel synthesis
            max_retries = 2
            last_err = None
            for attempt in range(max_retries):
                try:
                    communicate = edge_tts.Communicate(
                        text=text,
                        voice=voice_id,
                        rate=rate,
                        pitch=pitch
                    )
                    await asyncio.wait_for(communicate.save(output_path), timeout=25.0)

                    if os.path.exists(output_path) and os.path.getsize(output_path) > 100:
                        # Save to cache asynchronously
                        try:
                            shutil.copyfile(output_path, cache_file)
                        except Exception:
                            pass
                        return {
                            "success": True,
                            "output_path": output_path,
                            "cached": False,
                            "error": None
                        }
                except Exception as ex:
                    last_err = str(ex)
                    if attempt < max_retries - 1:
                        await asyncio.sleep(0.5 * (attempt + 1))

            return {
                "success": False,
                "output_path": None,
                "error": last_err or "Generated audio file is empty or missing"
            }
        except Exception as e:
            return {
                "success": False,
                "output_path": None,
                "error": str(e)
            }

