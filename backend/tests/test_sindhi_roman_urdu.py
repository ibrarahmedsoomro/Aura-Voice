import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.agents.script_intelligence import ScriptIntelligenceAgent
from app.agents.speech_planner import SpeechPlannerAgent
from app.agents.emotion_performance import EmotionPerformanceAgent
from app.agents.pronunciation import PronunciationAgent
from app.core.voice_catalog import (
    VOICE_CATALOG,
    rank_voices_for_script,
    resolve_voice_recommendation,
    get_all_voices
)

def test_roman_urdu_detection():
    agent = ScriptIntelligenceAgent()
    
    # Common everyday Roman Urdu sentences that previously failed as English
    r1, d1 = agent.detect_language("kya haal hai bhai sab theek hai")
    assert r1 == "roman_urdu", f"Expected roman_urdu, got {r1}"
    
    r2, d2 = agent.detect_language("aap kaise hain")
    assert r2 == "roman_urdu", f"Expected roman_urdu, got {r2}"
    
    r3, d3 = agent.detect_language("mujhe ye kaam zaroor karna hoga")
    assert r3 == "roman_urdu", f"Expected roman_urdu, got {r3}"
    
    r4, d4 = agent.detect_language("darwaza kholo aur aawaz suno")
    assert r4 == "roman_urdu", f"Expected roman_urdu, got {r4}"

def test_sindhi_and_roman_sindhi_detection():
    agent = ScriptIntelligenceAgent()
    
    # Roman Sindhi sentences
    s1, d1 = agent.detect_language("chha haal aahe bhalo ahyan")
    assert s1 == "roman_sindhi", f"Expected roman_sindhi, got {s1}"
    
    s2, d2 = agent.detect_language("tawahan jo naalo chha aahe, man theek ahyan")
    assert s2 == "roman_sindhi", f"Expected roman_sindhi, got {s2}"
    
    s3, d3 = agent.detect_language("asanjoo sindh bhalo watan aahe")
    assert s3 == "roman_sindhi", f"Expected roman_sindhi, got {s3}"
    
    # Perso-Arabic Sindhi script
    s_script, ds = agent.detect_language("سنڌي ٻولي خوبصورت آهي")
    assert s_script == "sd", f"Expected sd, got {s_script}"

def test_urdu_and_english_detection():
    agent = ScriptIntelligenceAgent()
    
    # Urdu Nastaliq script
    u1, _ = agent.detect_language("یہ ایک بہت خوبصورت کہانی ہے")
    assert u1 == "ur", f"Expected ur, got {u1}"
    
    # English
    e1, _ = agent.detect_language("Welcome to the cinematic audio narration studio.")
    assert e1 == "en", f"Expected en, got {e1}"

def test_sindhi_voice_catalog_and_ranking():
    all_voices = get_all_voices()
    sindhi_voices = [v for v in all_voices if v.language == "sd" or "sindhi" in v.name.lower()]
    assert len(sindhi_voices) >= 2, "Expected at least 2 Sindhi voice profiles in catalog"
    
    # Verify ranking for Sindhi
    ranked_sd = rank_voices_for_script("sindhi")
    assert ranked_sd[0]["voice"].language == "sd" or "sindhi" in ranked_sd[0]["voice"].name.lower()
    assert "Sindhi" in ranked_sd[0]["reason"]
    
    # Verify ranking for Roman Sindhi
    ranked_rsd = rank_voices_for_script("roman_sindhi")
    assert ranked_rsd[0]["voice"].language == "sd" or "sindhi" in ranked_rsd[0]["voice"].name.lower()

def test_roman_urdu_ranking():
    # Verify ranking for Roman Urdu
    ranked_rur = rank_voices_for_script("roman_urdu")
    assert ranked_rur[0]["voice"].language == "ur"
    assert "Urdu" in ranked_rur[0]["reason"]

def test_auto_cast_sindhi_and_roman_urdu():
    emotion_agent = EmotionPerformanceAgent()
    pronunciation_agent = PronunciationAgent()
    planner = SpeechPlannerAgent(emotion_agent, pronunciation_agent)
    
    # Auto cast for Sindhi
    cast_sd = planner.auto_cast_characters(["Narrator", "Sarah"], language="roman_sindhi")
    assert cast_sd["narrator"].voice_id in ["ur-PK-AsadNeural", "ur-PK-UzmaNeural"]
    assert "Sindhi" in cast_sd["narrator"].reason or "Regional" in cast_sd["narrator"].reason
    
    # Auto cast for Roman Urdu
    cast_ur = planner.auto_cast_characters(["Narrator", "Sarah"], language="roman_urdu")
    assert cast_ur["narrator"].voice_id in ["ur-PK-AsadNeural", "ur-PK-UzmaNeural"]
    assert "Urdu" in cast_ur["narrator"].reason

def test_user_exact_sentence_detection():
    agent = ScriptIntelligenceAgent()
    user_text = "agar urdu me jaise abhi typing kar raha hoon roman urdu hy wording bhalay hi english ki ho lekn language urdu aise hi agent nahi samjh raha hy still"
    lang, desc = agent.detect_language(user_text)
    assert lang == "roman_urdu", f"Expected roman_urdu, got {lang}"

def test_transliteration_to_spoken_script():
    agent = ScriptIntelligenceAgent()
    
    # Roman Urdu -> Urdu Nastaliq script for Edge-TTS
    t_ur = agent.transliterate_to_spoken_script("kya haal hai bhai sab theek hai", "roman_urdu")
    assert "کیا حال ہے بھائی سب ٹھیک ہے" in t_ur
    
    # Roman Sindhi -> Acoustic Perso-Arabic script for neural TTS
    t_sd = agent.transliterate_to_spoken_script("chha haal aahe bhalo ahyan", "roman_sindhi")
    assert "چھا حال آہے بھلو آہیاں" in t_sd

    # Raw Sindhi script -> Acoustic conversion
    t_raw = agent.transliterate_to_spoken_script("ڇا حال آهي", "sd")
    assert "چھا حال آہے" in t_raw

def test_speech_planner_preserves_text_and_populates_spoken():
    emotion_agent = EmotionPerformanceAgent()
    pronunciation_agent = PronunciationAgent()
    agent = ScriptIntelligenceAgent()
    planner = SpeechPlannerAgent(emotion_agent, pronunciation_agent, agent)
    
    scenes, chunks = planner.plan_speech(
        normalized_text="kya haal hai bhai sab theek hai",
        language="roman_urdu",
        base_voice_id="en-US-ChristopherNeural"  # Intentionally pass an English voice
    )
    assert len(chunks) >= 1
    # User's original script remains untouched in text and normalized_text
    assert chunks[0].text == "kya haal hai bhai sab theek hai"
    assert chunks[0].normalized_text == "kya haal hai bhai sab theek hai"
    # Spoken text is transliterated for TTS native delivery
    assert "کیا حال ہے بھائی سب ٹھیک ہے" in chunks[0].spoken_text
    # English voice Christopher was automatically aligned to native Urdu voice!
    assert chunks[0].voice_id == "ur-PK-AsadNeural"
