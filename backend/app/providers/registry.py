import logging
from typing import Dict, Any, Optional, List
from .base import BaseTTSProvider
from .edge_provider import EdgeTTSProvider
from .local_indic_provider import LocalIndicTTSProvider, LOCAL_VOICE_CONFIGS

logger = logging.getLogger("auravoice.registry")

LANGUAGE_CAPABILITIES: Dict[str, Dict[str, Any]] = {
    "sd": {
        "code": "sd",
        "name": "Sindhi",
        "native_name": "سنڌي",
        "script": "Perso-Arabic (52 letters)",
        "authentic_local_provider": "local-mms",
        "authentic_local_voice_id": "local-mms-snd",
        "online_provider_status": "UNSUPPORTED_ON_EDGE_TTS",
        "notes": "Edge-TTS has no native Sindhi voice. Authentic Sindhi is powered by local Meta MMS VITS on CPU."
    },
    "ur": {
        "code": "ur",
        "name": "Urdu",
        "native_name": "اردو",
        "script": "Perso-Arabic",
        "authentic_local_provider": "local-mms",
        "authentic_local_voice_id": "local-mms-urd",
        "online_provider_status": "SUPPORTED_ON_EDGE_TTS",
        "online_default_voice": "ur-PK-AsadNeural",
        "notes": "Supported natively on both Local CPU and Edge-TTS."
    },
    "hi": {
        "code": "hi",
        "name": "Hindi",
        "native_name": "हिन्दी",
        "script": "Devanagari",
        "authentic_local_provider": "local-mms",
        "authentic_local_voice_id": "local-mms-hin",
        "online_provider_status": "SUPPORTED_ON_EDGE_TTS",
        "online_default_voice": "hi-IN-MadhurNeural",
        "notes": "Supported natively on both Local CPU and Edge-TTS."
    },
    "en": {
        "code": "en",
        "name": "English",
        "native_name": "English",
        "script": "Latin",
        "authentic_local_provider": "local-mms",
        "authentic_local_voice_id": "local-mms-eng",
        "online_provider_status": "SUPPORTED_ON_EDGE_TTS",
        "online_default_voice": "en-US-ChristopherNeural",
        "notes": "Supported natively on both Local CPU and Edge-TTS."
    }
}

class ProviderRegistry:
    """
    Central registry for TTS providers.
    Supports local-first dispatch, voice-to-provider routing, and capability checks.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ProviderRegistry, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.edge_provider = EdgeTTSProvider()
        self.local_provider = LocalIndicTTSProvider()
        self._providers: Dict[str, BaseTTSProvider] = {
            "edge-tts": self.edge_provider,
            "local-mms": self.local_provider,
            "local": self.local_provider
        }
        self._initialized = True

    def get_provider(self, provider_id: str) -> BaseTTSProvider:
        """Retrieves provider by ID or falls back safely."""
        pid = (provider_id or "").lower()
        if pid in self._providers:
            return self._providers[pid]
        if "local" in pid:
            return self.local_provider
        return self.edge_provider

    def get_provider_for_voice(self, voice_id: str, requested_provider: Optional[str] = None) -> BaseTTSProvider:
        """
        Determines the correct provider for a given voice_id.
        - If voice_id starts with 'local-mms-' or is a local voice -> LocalIndicTTSProvider
        - If requested_provider is explicitly 'local' or 'local-mms' -> LocalIndicTTSProvider
        - Otherwise -> EdgeTTSProvider
        """
        if requested_provider in ["local", "local-mms"]:
            return self.local_provider

        if voice_id in LOCAL_VOICE_CONFIGS or voice_id.startswith("local-mms-"):
            return self.local_provider

        from ..core.voice_catalog import find_voice_by_id_or_profile
        voice = find_voice_by_id_or_profile(voice_id)
        if voice and voice.provider in ["local", "local-mms"]:
            return self.local_provider

        return self.edge_provider

    def list_providers(self) -> List[Dict[str, Any]]:
        """Returns metadata and health for all registered providers."""
        local_voices = self.local_provider.list_local_voices()
        cached_count = sum(1 for v in local_voices.values() if v.get("cached"))

        return [
            {
                "id": "local-mms",
                "name": "Meta MMS VITS (Local CPU)",
                "is_local": True,
                "requires_internet": False,
                "description": "Completely free, offline local speech synthesis on CPU. Authentic Sindhi, Urdu, Hindi & English.",
                "status": "ready" if cached_count > 0 else "weights_needed",
                "cached_models_count": cached_count,
                "total_models_count": len(local_voices),
                "voices": local_voices,
                "has_configured_token": bool(self.local_provider.get_configured_token())
            },
            {
                "id": "edge-tts",
                "name": "Edge-TTS Neural Cloud (Network Dependent)",
                "is_local": False,
                "requires_internet": True,
                "description": "High-fidelity cloud neural voices for English, Urdu, Hindi. Note: Edge-TTS does not support authentic Sindhi.",
                "status": "online",
                "cached_models_count": 0,
                "total_models_count": 0,
                "has_configured_token": False
            }
        ]

    def get_language_capabilities(self) -> Dict[str, Any]:
        """Returns language support breakdown with honest provider mappings."""
        return LANGUAGE_CAPABILITIES

# Global singleton instance
provider_registry = ProviderRegistry()
