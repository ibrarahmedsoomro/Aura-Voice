import asyncio
import os
import sys

# Ensure backend path is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agents.script_intelligence import ScriptIntelligenceAgent
from app.core.voice_catalog import verify_voice_consent_and_policy, rank_voices_for_script
from app.orchestrator.central_orchestrator import CentralOrchestrator
from app.models.schemas import GenerateVoiceRequest, RedoChunkRequest
from app.database.db import DatabaseManager

def test_script_intelligence():
    agent = ScriptIntelligenceAgent()

    # Test 1: Date & number normalization
    norm, lang, _ = agent.normalize("In 1944, B-25 bombers flew over WWII battlefields with 50% fuel.")
    assert "nineteen forty-four" in norm, f"Expected 1944 expanded, got: {norm}"
    assert "B twenty-five" in norm, f"Expected B-25 expanded, got: {norm}"
    assert "World War Two" in norm, f"Expected WWII expanded, got: {norm}"
    assert "fifty percent" in norm, f"Expected 50% expanded, got: {norm}"
    print("[PASS] Test 1: Script Intelligence Normalization passed.")

    # Test 2: Roman Urdu detection
    _, lang_urdu, _ = agent.normalize("Suddenly usne darwaza khola aur bola ke raat bohat khamosh hai.")
    assert lang_urdu == "roman_urdu", f"Expected roman_urdu, got: {lang_urdu}"
    print("[PASS] Test 2: Roman Urdu language detection passed.")

def test_voice_consent_gate():
    # Test 3: Celebrity cloning blocked
    blocked = verify_voice_consent_and_policy("Morgan Freeman")
    assert not blocked["allowed"], "Expected unauthorized celebrity clone to be blocked"
    print("[PASS] Test 3: Celebrity Voice Consent Gate passed.")

    # Test 4: Authorized voice allowed
    allowed = verify_voice_consent_and_policy("vox-cinematic-male")
    assert allowed["allowed"], "Expected authorized voice to be permitted"
    print("[PASS] Test 4: Authorized Voice Gate passed.")

def test_voice_ranking():
    # Test 5: Voice ranking for Urdu
    ranked = rank_voices_for_script("ur", "Documentary")
    assert ranked[0]["voice"].language == "ur", "Expected Urdu voice top ranked for Urdu"
    print("[PASS] Test 5: Voice Intelligence Ranking passed.")

async def test_end_to_end_generation_and_repair():
    o = CentralOrchestrator()
    db = DatabaseManager()

    # Test 6: Full generation
    req = GenerateVoiceRequest(
        text="The radar signal suddenly vanished. The commander ordered all units to stand by.",
        style_preference="Cinematic",
        emotion_mode="suspense"
    )
    result = await o.execute_voice_pipeline(req)
    assert result.status == "COMPLETED", f"Expected COMPLETED, got {result.status}"
    assert len(result.chunks) >= 2, f"Expected multiple chunks, got {len(result.chunks)}"
    assert os.path.exists(result.final_audio_mp3), "Expected final MP3 to exist on disk"
    assert os.path.exists(result.final_srt), "Expected final SRT to exist on disk"
    print(f"[PASS] Test 6: End-to-end voice generation passed (Project: {result.project_id}).")

    # Test 7: Surgical line redo
    redo_req = RedoChunkRequest(
        project_id=result.project_id,
        chunk_index=1,
        custom_speed=1.05
    )
    updated = await o.redo_single_chunk(redo_req)
    assert updated.status == "COMPLETED" or updated.progress_percentage == 100
    print(f"[PASS] Test 7: Surgical Line-by-Line Redo passed.")

    # Test 8: Database persistence check
    loaded = db.get_project(result.project_id)
    assert loaded is not None, "Expected project to be restored from SQLite database"
    assert len(loaded["chunks"]) >= 2, "Expected chunks to be loaded from database"
    print("[PASS] Test 8: Database persistence verified.")

if __name__ == "__main__":
    print("Running Aura Voice Test Suite...")
    test_script_intelligence()
    test_voice_consent_gate()
    test_voice_ranking()
    asyncio.run(test_end_to_end_generation_and_repair())
    print("\nALL 8 TESTS PASSED SUCCESSFULLY! [OK]")
