import os
import shutil
import hashlib
import asyncio
import logging
import subprocess
from typing import Dict, Any, Optional
import numpy as np

from .base import BaseTTSProvider

logger = logging.getLogger("auravoice.local_provider")

LOCAL_VOICE_CONFIGS: Dict[str, Dict[str, Any]] = {
    "local-mms-snd": {
        "repo_id": "facebook/mms-tts-snd",
        "language": "sd",
        "locale": "sd-PK",
        "gender": "Male",
        "name": "Meta MMS Sindhi (سنڌي مقامي)",
        "description": "Authentic native Sindhi neural voice running locally on CPU. Supports Sindhi Perso-Arabic script.",
        "sample_text": "سنڌ سلامت ساٿ سلامت، علم ۽ ادب جي ترقي اسان جو مقصد آهي."
    },
    "local-mms-urd": {
        "repo_id": "facebook/mms-tts-urd",
        "language": "ur",
        "locale": "ur-PK",
        "gender": "Male",
        "name": "Meta MMS Urdu (اردو مقامی)",
        "description": "Native Urdu neural voice running locally on CPU.",
        "sample_text": "السلام علیکم، یہ آواز مکمل طور پر آپ کے اپنے کمپیوٹر پر پروسیس ہوتی ہے۔"
    },
    "local-mms-hin": {
        "repo_id": "facebook/mms-tts-hin",
        "language": "hi",
        "locale": "hi-IN",
        "gender": "Male",
        "name": "Meta MMS Hindi (हिन्दी स्थानीय)",
        "description": "Native Hindi neural voice running locally on CPU with Devanagari support.",
        "sample_text": "नमस्ते, यह पूरी तरह से आपके कंप्यूटर पर स्थानीय रूप से चलने वाली आवाज़ है।"
    },
    "local-mms-eng": {
        "repo_id": "facebook/mms-tts-eng",
        "language": "en",
        "locale": "en-US",
        "gender": "Male",
        "name": "Meta MMS English (Local CPU)",
        "description": "Open-source English neural voice running locally on CPU.",
        "sample_text": "Hello! This voice is synthesized directly on your CPU without any cloud servers."
    }
}

class LocalIndicTTSProvider(BaseTTSProvider):
    """
    Local-first, completely free neural TTS provider using Meta MMS VITS models.
    Zero cloud API calls, zero subscriptions, 100% offline inference on local CPU.
    """

    def __init__(self, models_dir: Optional[str] = None, cache_dir: Optional[str] = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.models_dir = models_dir or os.path.join(base_dir, "storage", "models")
        self.cache_dir = cache_dir or os.path.join(base_dir, "storage", "cache", "tts_chunks")
        self.settings_file = os.path.join(base_dir, "storage", "settings.json")
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)

        self._loaded_models: Dict[str, Any] = {}
        self._loaded_tokenizers: Dict[str, Any] = {}
        self._inference_lock = asyncio.Lock()

    @property
    def provider_id(self) -> str:
        return "local-mms"

    @property
    def is_local(self) -> bool:
        return True

    def get_configured_token(self) -> Optional[str]:
        """Fetches HF_TOKEN from environment or settings.json."""
        token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
        if token:
            return token.strip()

        if os.path.exists(self.settings_file):
            try:
                import json
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    tok = data.get("hf_token")
                    if tok and str(tok).strip():
                        return str(tok).strip()
            except Exception:
                pass
        return None

    def _get_cache_path(self, text: str, voice_id: str, rate: str, pitch: str) -> str:
        cache_key = hashlib.sha256(f"LOCAL|{voice_id}|{rate}|{pitch}|{text}".encode("utf-8")).hexdigest()
        return os.path.join(self.cache_dir, f"{cache_key}.mp3")

    def is_model_cached(self, voice_id: str) -> bool:
        """Checks if model weights have been downloaded and are available locally."""
        if voice_id not in LOCAL_VOICE_CONFIGS:
            return False
        repo_id = LOCAL_VOICE_CONFIGS[voice_id]["repo_id"]
        
        # Check standard cache directory
        repo_slug = repo_id.replace("/", "--")
        hub_dir = os.path.join(self.models_dir, f"models--{repo_slug}")
        if os.path.exists(hub_dir) and os.path.isdir(hub_dir):
            snapshots_dir = os.path.join(hub_dir, "snapshots")
            if os.path.exists(snapshots_dir) and len(os.listdir(snapshots_dir)) > 0:
                return True

        # Check HuggingFace default home cache
        hf_home = os.environ.get("HF_HOME", os.path.expanduser("~/.cache/huggingface/hub"))
        default_hub_dir = os.path.join(hf_home, f"models--{repo_slug}")
        if os.path.exists(default_hub_dir) and os.path.isdir(default_hub_dir):
            snapshots_dir = os.path.join(default_hub_dir, "snapshots")
            if os.path.exists(snapshots_dir) and len(os.listdir(snapshots_dir)) > 0:
                return True

        return False

    def get_model_status(self, voice_id: str) -> Dict[str, Any]:
        """Returns status of a specific local model."""
        if voice_id not in LOCAL_VOICE_CONFIGS:
            return {"exists": False, "supported": False, "cached": False}
        
        cfg = LOCAL_VOICE_CONFIGS[voice_id]
        is_cached = self.is_model_cached(voice_id)
        is_loaded = cfg["repo_id"] in self._loaded_models

        return {
            "voice_id": voice_id,
            "name": cfg["name"],
            "repo_id": cfg["repo_id"],
            "language": cfg["language"],
            "supported": True,
            "cached": is_cached,
            "loaded_in_memory": is_loaded,
            "is_local": True
        }

    def list_local_voices(self) -> Dict[str, Dict[str, Any]]:
        """Lists all local voices with their cached/download status."""
        result = {}
        for vid in LOCAL_VOICE_CONFIGS:
            result[vid] = self.get_model_status(vid)
        return result

    def _load_model_sync(self, repo_id: str, voice_id: str = ""):
        """Loads VITS model and tokenizer from local cache or Hub (synchronous)."""
        if repo_id in self._loaded_models:
            return self._loaded_models[repo_id], self._loaded_tokenizers[repo_id]

        from transformers import VitsModel, VitsTokenizer
        token = self.get_configured_token()

        # 1. If cached locally, load purely offline (0ms, no network calls)
        if voice_id and self.is_model_cached(voice_id):
            try:
                tokenizer = VitsTokenizer.from_pretrained(
                    repo_id,
                    cache_dir=self.models_dir,
                    local_files_only=True
                )
                model = VitsModel.from_pretrained(
                    repo_id,
                    cache_dir=self.models_dir,
                    local_files_only=True
                )
                model.eval()
                self._loaded_models[repo_id] = model
                self._loaded_tokenizers[repo_id] = tokenizer
                return model, tokenizer
            except Exception:
                pass

        # 2. Not cached: If no token is provided, fail immediately instead of hanging in 25-second 429 retry loop
        if not token:
            raise RuntimeError(
                f"Local model weights for '{voice_id or repo_id}' are not yet downloaded. "
                "Hugging Face rate-limits anonymous downloads (HTTP 429). "
                "Please configure a free Hugging Face token in Settings, or use an online voice."
            )

        # 3. Download with authorized token
        logger.info(f"Downloading/loading local VITS model for '{repo_id}' from cache_dir '{self.models_dir}'...")
        tokenizer = VitsTokenizer.from_pretrained(
            repo_id,
            cache_dir=self.models_dir,
            token=token
        )
        model = VitsModel.from_pretrained(
            repo_id,
            cache_dir=self.models_dir,
            token=token
        )
        model.eval()

        self._loaded_models[repo_id] = model
        self._loaded_tokenizers[repo_id] = tokenizer
        return model, tokenizer

    def _parse_rate_to_tempo(self, rate_str: str) -> float:
        """Parses rate percentage string (e.g. '+10%', '-5%') to tempo factor (e.g. 1.1, 0.95)."""
        try:
            cleaned = rate_str.strip().replace("%", "")
            if cleaned.startswith("+"):
                cleaned = cleaned[1:]
            pct = float(cleaned)
            tempo = 1.0 + (pct / 100.0)
            return max(0.5, min(2.0, tempo))
        except Exception:
            return 1.0

    def _run_inference_sync(
        self,
        text: str,
        repo_id: str,
        voice_id: str,
        rate: str,
        output_path: str
    ) -> None:
        """Synchronous CPU inference and audio writing with FFmpeg tempo modulation."""
        import torch
        import scipy.io.wavfile

        model, tokenizer = self._load_model_sync(repo_id, voice_id=voice_id)

        # Tokenize and run forward pass
        inputs = tokenizer(text, return_tensors="pt")
        with torch.no_grad():
            output = model(**inputs).waveform

        wav_tensor = output.cpu().float()
        wav_numpy = wav_tensor.squeeze().numpy()
        sampling_rate = int(getattr(model.config, "sampling_rate", 16000))

        # Normalize and clip
        max_val = np.max(np.abs(wav_numpy))
        if max_val > 0:
            wav_numpy = wav_numpy / max_val * 0.95
        int16_audio = (wav_numpy * 32767).astype(np.int16)

        # Temporary wav path
        temp_wav = output_path + ".temp.wav"
        scipy.io.wavfile.write(temp_wav, rate=sampling_rate, data=int16_audio)

        try:
            tempo = self._parse_rate_to_tempo(rate)
            # Use FFmpeg to apply tempo and convert to final output format (mp3 or wav)
            cmd = ["ffmpeg", "-y", "-i", temp_wav]
            if abs(tempo - 1.0) > 0.02:
                cmd.extend(["-filter:a", f"atempo={tempo:.2f}"])
            if output_path.endswith(".mp3"):
                cmd.extend(["-b:a", "192k", "-c:a", "libmp3lame", output_path])
            else:
                cmd.append(output_path)

            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0 or not os.path.exists(output_path) or os.path.getsize(output_path) < 100:
                # Fallback: simple copy if ffmpeg fails
                shutil.copyfile(temp_wav, output_path)
        finally:
            if os.path.exists(temp_wav):
                try:
                    os.remove(temp_wav)
                except Exception:
                    pass

    async def synthesize_chunk(
        self,
        text: str,
        voice_id: str,
        rate: str = "+0%",
        pitch: str = "+0Hz",
        output_path: str = ""
    ) -> Dict[str, Any]:
        """
        Synthesizes a chunk of text using the local VITS model.
        Returns {"success": bool, "output_path": str, "cached": bool, "error": Optional[str]}.
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            cache_file = self._get_cache_path(text, voice_id, rate, pitch)

            # Check persistent chunk cache
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

            if voice_id not in LOCAL_VOICE_CONFIGS:
                return {
                    "success": False,
                    "output_path": None,
                    "error": f"Unknown local voice ID '{voice_id}'. Supported: {list(LOCAL_VOICE_CONFIGS.keys())}"
                }

            repo_id = LOCAL_VOICE_CONFIGS[voice_id]["repo_id"]

            async with self._inference_lock:
                await asyncio.to_thread(
                    self._run_inference_sync,
                    text=text,
                    repo_id=repo_id,
                    voice_id=voice_id,
                    rate=rate,
                    output_path=output_path
                )

            if os.path.exists(output_path) and os.path.getsize(output_path) > 100:
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
            else:
                return {
                    "success": False,
                    "output_path": None,
                    "error": "Synthesis produced empty or missing audio file."
                }

        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "Too Many Requests" in err_msg:
                user_msg = (
                    f"Hugging Face rate-limited anonymous download for '{voice_id}'. "
                    f"Please add your free Hugging Face token in Settings to enable local download."
                )
            elif "not found" in err_msg.lower() or "could not find" in err_msg.lower():
                user_msg = f"Local model weights for '{voice_id}' could not be loaded: {err_msg}"
            else:
                user_msg = f"Local inference error: {err_msg}"
            
            logger.error(f"Local TTS synthesis failed: {err_msg}")
            return {
                "success": False,
                "output_path": None,
                "error": user_msg
            }
