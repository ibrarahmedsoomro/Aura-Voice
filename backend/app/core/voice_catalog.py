from typing import List, Optional, Dict, Any
from ..models.schemas import VoiceProfile

VOICE_CATALOG: Dict[str, VoiceProfile] = {
    # English Voices
    "vox-cinematic-male": VoiceProfile(
        voice_id="en-US-ChristopherNeural",
        name="Aura Christopher",
        gender="Male",
        language="en",
        locale="en-US",
        style="Cinematic",
        provider="edge-tts",
        license_type="LICENSED_PROVIDER",
        description="Deep, resonant, dramatic narrator ideal for movies, WWII history, and horror trailers.",
        is_authorized=True,
        qc_rating=0.99
    ),
    "vox-documentary-male": VoiceProfile(
        voice_id="en-US-GuyNeural",
        name="Aura Guy",
        gender="Male",
        language="en",
        locale="en-US",
        style="Documentary",
        provider="edge-tts",
        license_type="LICENSED_PROVIDER",
        description="Authoritative, calm, clear documentary narrator suited for long-form explainers.",
        is_authorized=True,
        qc_rating=0.98
    ),
    "vox-storyteller-female": VoiceProfile(
        voice_id="en-US-JennyNeural",
        name="Aura Jenny",
        gender="Female",
        language="en",
        locale="en-US",
        style="Storyteller",
        provider="edge-tts",
        license_type="LICENSED_PROVIDER",
        description="Warm, highly expressive storytelling voice with natural inflection and emotional range.",
        is_authorized=True,
        qc_rating=0.98
    ),
    "vox-dramatic-female": VoiceProfile(
        voice_id="en-US-AriaNeural",
        name="Aura Aria",
        gender="Female",
        language="en",
        locale="en-US",
        style="Dramatic",
        provider="edge-tts",
        license_type="LICENSED_PROVIDER",
        description="Dynamic, crisp voice with exceptional pacing for thrilling stories and commercial narration.",
        is_authorized=True,
        qc_rating=0.97
    ),
    "vox-british-historian": VoiceProfile(
        voice_id="en-GB-RyanNeural",
        name="Aura Ryan",
        gender="Male",
        language="en",
        locale="en-GB",
        style="Documentary",
        provider="edge-tts",
        license_type="LICENSED_PROVIDER",
        description="Sophisticated British accent, excellent for vintage war archives, literature, and mystery.",
        is_authorized=True,
        qc_rating=0.97
    ),
    "vox-modern-podcast": VoiceProfile(
        voice_id="en-US-EricNeural",
        name="Aura Eric",
        gender="Male",
        language="en",
        locale="en-US",
        style="Conversational",
        provider="edge-tts",
        license_type="LICENSED_PROVIDER",
        description="Youthful, engaging, fast-paced voice tailored for short-form Reels, TikToks, and podcasts.",
        is_authorized=True,
        qc_rating=0.96
    ),
    
    # Urdu Voices (Authentic PK)
    "vox-urdu-asad": VoiceProfile(
        voice_id="ur-PK-AsadNeural",
        name="Aura Asad",
        gender="Male",
        language="ur",
        locale="ur-PK",
        style="Documentary",
        provider="edge-tts",
        license_type="LICENSED_PROVIDER",
        description="Solemn, clear Urdu narrator suitable for stories, history, poetry, and Roman Urdu scripts.",
        is_authorized=True,
        qc_rating=0.98
    ),
    "vox-urdu-uzma": VoiceProfile(
        voice_id="ur-PK-UzmaNeural",
        name="Aura Uzma",
        gender="Female",
        language="ur",
        locale="ur-PK",
        style="Storyteller",
        provider="edge-tts",
        license_type="LICENSED_PROVIDER",
        description="Gentle, eloquent Urdu voice with pristine enunciation for audiobooks and dramatic tales.",
        is_authorized=True,
        qc_rating=0.98
    ),
    
    # Hindi / Hinglish Voices
    "vox-hindi-madhur": VoiceProfile(
        voice_id="hi-IN-MadhurNeural",
        name="Aura Madhur",
        gender="Male",
        language="hi",
        locale="hi-IN",
        style="Storyteller",
        provider="edge-tts",
        license_type="LICENSED_PROVIDER",
        description="Dynamic Hindi and Hinglish narrator with vivid tone modulation.",
        is_authorized=True,
        qc_rating=0.97
    ),
    "vox-hindi-swara": VoiceProfile(
        voice_id="hi-IN-SwaraNeural",
        name="Aura Swara",
        gender="Female",
        language="hi",
        locale="hi-IN",
        style="Conversational",
        provider="edge-tts",
        license_type="LICENSED_PROVIDER",
        description="Warm, versatile Hindi voice for narrative explainers and character dialogue.",
        is_authorized=True,
        qc_rating=0.97
    )
}

def get_all_voices() -> List[VoiceProfile]:
    return list(VOICE_CATALOG.values())

def find_voice_by_id_or_profile(voice_id: str) -> Optional[VoiceProfile]:
    for key, v in VOICE_CATALOG.items():
        if key == voice_id or v.voice_id == voice_id:
            return v
    return None

def rank_voices_for_script(
    language: str,
    style_preference: str = "Cinematic",
    user_preferred_voice: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Ranks candidate voices based on language compatibility, style match,
    QC history, and user preferences (Module 5 & 14).
    """
    ranked = []
    lang_lower = language.lower()
    style_lower = style_preference.lower()

    for v in VOICE_CATALOG.values():
        score = 0.5
        reasons = []

        # Language match
        if ("ur" in lang_lower or "roman" in lang_lower) and v.language == "ur":
            score += 0.35
            reasons.append("Native Urdu / Roman Urdu enunciation")
        elif "hi" in lang_lower and v.language == "hi":
            score += 0.35
            reasons.append("Native Hindi cadence")
        elif v.language == "en" and "ur" not in lang_lower and "hi" not in lang_lower:
            score += 0.30
            reasons.append("Native English clarity")
        elif v.language == "en":
            score += 0.10

        # Style match
        if style_lower in v.style.lower() or style_lower in v.description.lower():
            score += 0.15
            reasons.append(f"High {v.style} storytelling suitability")

        # QC rating bonus
        score += (v.qc_rating - 0.90) * 0.5

        # User favorite bonus
        if user_preferred_voice and (user_preferred_voice == v.voice_id or user_preferred_voice in v.name):
            score += 0.05
            reasons.append("User preference match")

        confidence = min(0.99, max(0.60, round(score, 2)))
        ranked.append({
            "voice": v,
            "confidence": confidence,
            "reason": "; ".join(reasons) or f"Solid {v.style} match"
        })

    # Sort descending by confidence
    ranked.sort(key=lambda x: x["confidence"], reverse=True)
    return ranked

def resolve_voice_recommendation(language: str, style_pref: str = "Cinematic") -> VoiceProfile:
    ranked = rank_voices_for_script(language, style_pref)
    return ranked[0]["voice"]

def verify_voice_consent_and_policy(voice_id_or_name: str) -> Dict[str, Any]:
    prohibited_keywords = [
        "morgan freeman", "david attenborough", "joe rogan", "trump", "obama", 
        "elon musk", "celebrity", "clone actor", "cloned voice"
    ]
    name_check = voice_id_or_name.lower()
    for kw in prohibited_keywords:
        if kw in name_check:
            return {
                "allowed": False,
                "reason": f"Direct imitation/cloning of '{kw}' is prohibited by safety policy. Using authorized high-quality style profile instead.",
                "substitute_profile": VOICE_CATALOG["vox-cinematic-male"]
            }
    return {"allowed": True, "reason": "Voice source verified and authorized."}
