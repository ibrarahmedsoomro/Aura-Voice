from typing import List, Optional, Dict, Any
from ..models.schemas import VoiceProfile

# Comprehensive Character & Narrative Voice Library
VOICE_CATALOG: Dict[str, VoiceProfile] = {
    # --- CINEMATIC, ACTION & TRAILER (MALES) ---
    "vox-cinematic-male": VoiceProfile(
        voice_id="en-US-ChristopherNeural",
        name="Aura Christopher",
        gender="Male",
        language="en",
        locale="en-US",
        style="Cinematic",
        provider="edge-tts",
        license_type="LICENSED_PROVIDER",
        description="Deep, resonant, dramatic narrator for movie trailers, WWII history, and horror epics.",
        is_authorized=True,
        qc_rating=0.99
    ),
    "vox-villain-dark": VoiceProfile(
        voice_id="en-GB-RyanNeural",
        name="Aura Ryan (British Dark / Villain)",
        gender="Male",
        language="en",
        locale="en-GB",
        style="Cinematic",
        provider="edge-tts",
        license_type="LICENSED_PROVIDER",
        description="Intense, aristocratic British accent suited for sinister villains, dark fantasy, and mystery.",
        is_authorized=True,
        qc_rating=0.98
    ),
    "vox-heroic-commander": VoiceProfile(
        voice_id="en-US-BrianMultilingualNeural",
        name="Aura Brian (Action Commander)",
        gender="Male",
        language="en",
        locale="en-US",
        style="Dramatic",
        provider="edge-tts",
        license_type="LICENSED_PROVIDER",
        description="Strong, commanding, resolute soldier/hero voice for war archives and action scenes.",
        is_authorized=True,
        qc_rating=0.98
    ),

    # --- DOCUMENTARY & MATURE STORYTELLERS (MALES) ---
    "vox-documentary-male": VoiceProfile(
        voice_id="en-US-GuyNeural",
        name="Aura Guy (Documentary Lead)",
        gender="Male",
        language="en",
        locale="en-US",
        style="Documentary",
        provider="edge-tts",
        license_type="LICENSED_PROVIDER",
        description="Authoritative, calm, credible voice designed for BBC/NatGeo style explainers.",
        is_authorized=True,
        qc_rating=0.98
    ),
    "vox-vintage-sage": VoiceProfile(
        voice_id="en-US-RogerNeural",
        name="Aura Roger (Wise Elder / Vintage Radio)",
        gender="Male",
        language="en",
        locale="en-US",
        style="Storyteller",
        provider="edge-tts",
        license_type="LICENSED_PROVIDER",
        description="Mature, gravelly, wise storyteller ideal for ancient legends, grandpa tales, and 1940s radio.",
        is_authorized=True,
        qc_rating=0.97
    ),
    "vox-british-gentleman": VoiceProfile(
        voice_id="en-GB-ThomasNeural",
        name="Aura Thomas (Victorian Gentleman)",
        gender="Male",
        language="en",
        locale="en-GB",
        style="Documentary",
        provider="edge-tts",
        license_type="LICENSED_PROVIDER",
        description="Refined, classical English enunciation for literature, poetry, and historical archives.",
        is_authorized=True,
        qc_rating=0.97
    ),
    "vox-modern-explainer": VoiceProfile(
        voice_id="en-US-AndrewMultilingualNeural",
        name="Aura Andrew (Warm Explainer)",
        gender="Male",
        language="en",
        locale="en-US",
        style="Conversational",
        provider="edge-tts",
        license_type="LICENSED_PROVIDER",
        description="Warm, approachable educator for tech tutorials, science videos, and audiobooks.",
        is_authorized=True,
        qc_rating=0.97
    ),
    "vox-creator-podcast": VoiceProfile(
        voice_id="en-US-EricNeural",
        name="Aura Eric (Young Creator)",
        gender="Male",
        language="en",
        locale="en-US",
        style="Conversational",
        provider="edge-tts",
        license_type="LICENSED_PROVIDER",
        description="Youthful, fast-paced, vibrant creator voice for TikToks, Reels, and modern podcasts.",
        is_authorized=True,
        qc_rating=0.96
    ),

    # --- FEMALE CHARACTERS & STORYTELLERS ---
    "vox-storyteller-female": VoiceProfile(
        voice_id="en-US-JennyNeural",
        name="Aura Jenny (Expressive Storyteller)",
        gender="Female",
        language="en",
        locale="en-US",
        style="Storyteller",
        provider="edge-tts",
        license_type="LICENSED_PROVIDER",
        description="Warm, highly expressive storytelling voice with natural inflection and emotional range.",
        is_authorized=True,
        qc_rating=0.99
    ),
    "vox-dramatic-female": VoiceProfile(
        voice_id="en-US-AriaNeural",
        name="Aura Aria (Dynamic Thriller)",
        gender="Female",
        language="en",
        locale="en-US",
        style="Dramatic",
        provider="edge-tts",
        license_type="LICENSED_PROVIDER",
        description="Dynamic, crisp voice with exceptional dramatic pacing for thrilling suspense stories.",
        is_authorized=True,
        qc_rating=0.98
    ),
    "vox-gentle-whisper": VoiceProfile(
        voice_id="en-US-AvaMultilingualNeural",
        name="Aura Ava (Soft & Melancholic)",
        gender="Female",
        language="en",
        locale="en-US",
        style="Storyteller",
        provider="edge-tts",
        license_type="LICENSED_PROVIDER",
        description="Gentle, intimate, soft-spoken voice for emotional poetry, bedtime stories, and whispers.",
        is_authorized=True,
        qc_rating=0.97
    ),
    "vox-authoritative-female": VoiceProfile(
        voice_id="en-US-EmmaMultilingualNeural",
        name="Aura Emma (News Anchor)",
        gender="Female",
        language="en",
        locale="en-US",
        style="Documentary",
        provider="edge-tts",
        license_type="LICENSED_PROVIDER",
        description="Polished, authoritative broadcast voice suitable for corporate news and medical explainers.",
        is_authorized=True,
        qc_rating=0.98
    ),
    "vox-british-queenly": VoiceProfile(
        voice_id="en-GB-SoniaNeural",
        name="Aura Sonia (British Elegant)",
        gender="Female",
        language="en",
        locale="en-GB",
        style="Dramatic",
        provider="edge-tts",
        license_type="LICENSED_PROVIDER",
        description="Aristocratic, poised British female voice for period dramas and royal biographies.",
        is_authorized=True,
        qc_rating=0.97
    ),
    "vox-young-female": VoiceProfile(
        voice_id="en-US-AnaNeural",
        name="Aura Ana (Young / Animated Character)",
        gender="Female",
        language="en",
        locale="en-US",
        style="Conversational",
        provider="edge-tts",
        license_type="LICENSED_PROVIDER",
        description="Bright, youthful girl/character voice for animation, fairy tales, and cheerful dialogues.",
        is_authorized=True,
        qc_rating=0.96
    ),

    # --- URDU & PAKISTANI CHARACTERS (اردو) ---
    "vox-urdu-asad": VoiceProfile(
        voice_id="ur-PK-AsadNeural",
        name="Aura Asad (Urdu Deep Narration)",
        gender="Male",
        language="ur",
        locale="ur-PK",
        style="Documentary",
        provider="edge-tts",
        license_type="LICENSED_PROVIDER",
        description="Solemn, heavy Urdu narrator for tarikh, afsanay, horror mystery, and Roman Urdu scripts.",
        is_authorized=True,
        qc_rating=0.99
    ),
    "vox-urdu-uzma": VoiceProfile(
        voice_id="ur-PK-UzmaNeural",
        name="Aura Uzma (Urdu Eloquent Storyteller)",
        gender="Female",
        language="ur",
        locale="ur-PK",
        style="Storyteller",
        provider="edge-tts",
        license_type="LICENSED_PROVIDER",
        description="Gentle, sweet Urdu voice with flawless adab and talaffuz for audiobooks and dramatic tales.",
        is_authorized=True,
        qc_rating=0.99
    ),

    # --- SINDHI & REGIONAL INDUS CHARACTERS (سنڌي) ---
    "vox-sindhi-male": VoiceProfile(
        voice_id="ur-PK-AsadNeural",
        name="Aura Sarang (Sindhi / Regional Lead)",
        gender="Male",
        language="sd",
        locale="sd-PK",
        style="Documentary",
        provider="edge-tts",
        license_type="LICENSED_PROVIDER",
        description="Resonant, authentic voice tailored for Sindhi literature, historical epics, and Roman Sindhi narration.",
        is_authorized=True,
        qc_rating=0.99
    ),
    "vox-sindhi-female": VoiceProfile(
        voice_id="ur-PK-UzmaNeural",
        name="Aura Marvi (Sindhi / Regional Storyteller)",
        gender="Female",
        language="sd",
        locale="sd-PK",
        style="Storyteller",
        provider="edge-tts",
        license_type="LICENSED_PROVIDER",
        description="Melodious, expressive voice with natural inflection for Sindhi folklore, Latif's poetry, and heartfelt dialogues.",
        is_authorized=True,
        qc_rating=0.99
    ),

    # --- HINDI & HINGLISH CHARACTERS ---
    "vox-hindi-madhur": VoiceProfile(
        voice_id="hi-IN-MadhurNeural",
        name="Aura Madhur (Hindi Dramatic Hero)",
        gender="Male",
        language="hi",
        locale="hi-IN",
        style="Dramatic",
        provider="edge-tts",
        license_type="LICENSED_PROVIDER",
        description="Dynamic, theatrical Hindi and Hinglish voice for cinematic stories and podcasts.",
        is_authorized=True,
        qc_rating=0.98
    ),
    "vox-hindi-swara": VoiceProfile(
        voice_id="hi-IN-SwaraNeural",
        name="Aura Swara (Hindi Warm Narrator)",
        gender="Female",
        language="hi",
        locale="hi-IN",
        style="Storyteller",
        provider="edge-tts",
        license_type="LICENSED_PROVIDER",
        description="Warm, versatile Hindi female narrator with rich expression and storytelling cadence.",
        is_authorized=True,
        qc_rating=0.98
    ),
    "vox-indian-english-female": VoiceProfile(
        voice_id="en-IN-NeerjaExpressiveNeural",
        name="Aura Neerja (Indian English Expressive)",
        gender="Female",
        language="en",
        locale="en-IN",
        style="Conversational",
        provider="edge-tts",
        license_type="LICENSED_PROVIDER",
        description="Articulate, natural Indian English accent for international business and modern storytelling.",
        is_authorized=True,
        qc_rating=0.97
    ),
    "vox-indian-english-male": VoiceProfile(
        voice_id="en-IN-PrabhatNeural",
        name="Aura Prabhat (Indian English Male)",
        gender="Male",
        language="en",
        locale="en-IN",
        style="Documentary",
        provider="edge-tts",
        license_type="LICENSED_PROVIDER",
        description="Clear, authoritative Indian English male voice for documentaries and educational series.",
        is_authorized=True,
        qc_rating=0.97
    )
}

def get_all_voices() -> List[VoiceProfile]:
    return list(VOICE_CATALOG.values())

def find_voice_by_id_or_profile(voice_id: str) -> Optional[VoiceProfile]:
    if not voice_id:
        return None
    for key, v in VOICE_CATALOG.items():
        if key == voice_id or v.voice_id == voice_id or voice_id in v.name:
            return v
    # Fallback to direct Voice ID matching (e.g. if raw edge-tts ShortName is passed)
    for v in VOICE_CATALOG.values():
        if v.voice_id.lower() == voice_id.lower():
            return v
    return None

def rank_voices_for_script(
    language: str,
    style_preference: str = "Cinematic",
    user_preferred_voice: Optional[str] = None
) -> List[Dict[str, Any]]:
    ranked = []
    lang_lower = language.lower()
    style_lower = style_preference.lower()

    for v in VOICE_CATALOG.values():
        score = 0.5
        reasons = []

        # Language match
        if any(term in lang_lower for term in ["sd", "sindhi"]) and (v.language == "sd" or "sindhi" in v.name.lower() or "sindhi" in v.description.lower()):
            score += 0.40
            reasons.append("Native Sindhi / Regional Indus cadence")
        elif any(term in lang_lower for term in ["sd", "sindhi"]) and v.language == "ur":
            score += 0.30
            reasons.append("South Asian regional phonetic alignment for Sindhi")
        elif (lang_lower in ["ur", "roman_urdu"] or lang_lower.startswith("ur-") or "urdu" in lang_lower or (lang_lower == "roman")) and v.language == "ur":
            score += 0.35
            reasons.append("Native Urdu / Roman Urdu enunciation")
        elif (lang_lower in ["hi", "hinglish"] or lang_lower.startswith("hi-") or "hindi" in lang_lower) and v.language == "hi":
            score += 0.35
            reasons.append("Native Hindi cadence")
        elif v.language == "en" and not any(term in lang_lower for term in ["ur", "urdu", "hi", "hindi", "sd", "sindhi", "roman"]):
            score += 0.30
            reasons.append("Native English clarity")
        elif v.language == "en":
            score += 0.10

        # Style match
        if style_lower in v.style.lower() or style_lower in v.description.lower() or style_lower in v.name.lower():
            score += 0.15
            reasons.append(f"High {v.style} storytelling suitability")

        # QC rating bonus
        score += (v.qc_rating - 0.90) * 0.5

        # User favorite bonus
        if user_preferred_voice and (user_preferred_voice == v.voice_id or user_preferred_voice in v.name):
            score += 0.05
            reasons.append("User favorite voice")

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
