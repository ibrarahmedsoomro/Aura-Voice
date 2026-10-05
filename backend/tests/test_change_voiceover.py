import asyncio
import os
import sys

# Ensure backend path is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.orchestrator.central_orchestrator import CentralOrchestrator
from app.models.schemas import GenerateVoiceRequest

async def run_test():
    print("=== TEST: CHANGE VOICEOVER & CHARACTER REPLACEMENT ===")
    orchestrator = CentralOrchestrator()

    script = """Narrator: The dark forest was eerily quiet.
Commander: Keep your flashlights pointed forward.
Witch: Turn back before it is too late!
Commander: Maintain your positions!"""

    req = GenerateVoiceRequest(
        text=script,
        voice_id="auto",
        style_preference="Cinematic"
    )

    proj_id = "TEST-REPLACE-VOICE-001"
    print(f"Generating initial multi-character project: {proj_id}...")
    state = await orchestrator.execute_voice_pipeline(req, existing_project_id=proj_id)
    assert state.status == "COMPLETED"
    print(f"Initial generation complete. Total chunks: {len(state.chunks)}")

    # Check Commander's initial voice
    proj = orchestrator.db.get_project(proj_id)
    commander_chunks = [c for c in proj["chunks"] if (c.get("speaker") or "").lower() == "commander"]
    assert len(commander_chunks) == 2, f"Expected 2 Commander lines, got {len(commander_chunks)}"
    initial_commander_voice = commander_chunks[0]["voice_id"]
    print(f"Commander's initial voice: {initial_commander_voice}")

    # 1. Replace Commander's voiceover with en-US-RogerNeural
    new_voice = "en-US-RogerNeural"
    print(f"\n[TEST 1] Replacing Commander's voiceover with '{new_voice}'...")
    updated_proj = await orchestrator.replace_character_voice(
        project_id=proj_id,
        character_id="commander",
        new_voice_id=new_voice
    )

    # Verify Commander lines updated
    updated_commander_chunks = [c for c in updated_proj["chunks"] if (c.get("speaker") or "").lower() == "commander"]
    for c in updated_commander_chunks:
        assert c["voice_id"] == new_voice, f"Chunk {c['chunk_index']} expected {new_voice}, got {c['voice_id']}"
    print(f"  [OK] Both Commander lines updated to {new_voice}!")

    # Verify Narrator line untouched
    narrator_chunk = next(c for c in updated_proj["chunks"] if (c.get("speaker") or "").lower() == "narrator")
    assert narrator_chunk["voice_id"] != new_voice, "Narrator voice was erroneously overwritten!"
    print(f"  [OK] Narrator voice remained isolated: {narrator_chunk['voice_id']}")

    # Verify Witch line untouched
    witch_chunk = next(c for c in updated_proj["chunks"] if (c.get("speaker") or "").lower() == "witch")
    assert witch_chunk["voice_id"] != new_voice, "Witch voice was erroneously overwritten!"
    print(f"  [OK] Witch voice remained isolated: {witch_chunk['voice_id']}")

    # Verify master audio exists and is playable
    assert os.path.exists(updated_proj["final_audio_mp3"]), "Master MP3 does not exist"
    assert os.path.getsize(updated_proj["final_audio_mp3"]) > 1000, "Master MP3 too small"
    print(f"  [OK] Master audio reassembled & remastered ({os.path.getsize(updated_proj['final_audio_mp3'])} bytes)")

    # 2. Test full project voiceover replacement
    full_new_voice = "en-US-GuyNeural"
    print(f"\n[TEST 2] Replacing entire project voiceover with '{full_new_voice}'...")
    full_updated = await orchestrator.replace_project_voice(
        project_id=proj_id,
        new_voice_id=full_new_voice
    )
    for c in full_updated["chunks"]:
        assert c["voice_id"] == full_new_voice, f"Chunk {c['chunk_index']} not updated to {full_new_voice}"
    assert full_updated["voice_id"] == full_new_voice
    assert os.path.exists(full_updated["final_audio_mp3"])
    print(f"  [OK] All chunks and master audio updated to {full_new_voice} ({os.path.getsize(full_updated['final_audio_mp3'])} bytes)")

    print("\n[RESULT] ALL CHANGE VOICEOVER TESTS PASSED 100%!")

if __name__ == "__main__":
    asyncio.run(run_test())
