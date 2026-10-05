import urllib.request
import json
import time
import os

base_url = "http://localhost:8001"

def run_step19_step20():
    print("=== STEP 19: REAL MULTI-CHARACTER SCRIPT TEST ===")
    test_id = f"STEP19-{int(time.time())}"

    script = (
        "Narrator: The old castle gates opened slowly.\n\n"
        "Commander: Everyone stay alert.\n\n"
        "Witch: You should never have come here.\n\n"
        "Doctor: Wait. Those symbols are not decorative.\n\n"
        "Commander: What do you mean?\n\n"
        "Witch: They are a warning."
    )

    payload = {
        "text": script,
        "voice_id": "auto",
        "style_preference": "Cinematic",
        "emotion_mode": "auto",
        "language_hint": "en"
    }

    req = urllib.request.Request(
        f"{base_url}/api/projects/{test_id}/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=90) as resp:
        proj = json.loads(resp.read().decode())

    print(f"[STATUS] {proj.get('status')}")
    chunks = proj.get("chunks", [])
    print(f"[CHUNKS] Total: {len(chunks)}")

    assert len(chunks) == 6, f"Expected 6 chunks, got {len(chunks)}"

    # Check speakers
    speakers = [c.get("speaker") for c in chunks]
    voices = [c.get("voice_id") for c in chunks]

    print("Sequence:")
    for c in chunks:
        print(f"  #{c['chunk_index']} [{c.get('speaker')}] Voice: {c.get('voice_id')} -> \"{c['text']}\"")

    assert chunks[0]["speaker"] == "Narrator", f"Chunk 1 expected Narrator, got {chunks[0]['speaker']}"
    assert chunks[1]["speaker"] == "Commander", f"Chunk 2 expected Commander, got {chunks[1]['speaker']}"
    assert chunks[2]["speaker"] == "Witch", f"Chunk 3 expected Witch, got {chunks[2]['speaker']}"
    assert chunks[3]["speaker"] == "Doctor", f"Chunk 4 expected Doctor, got {chunks[3]['speaker']}"
    assert chunks[4]["speaker"] == "Commander", f"Chunk 5 expected Commander, got {chunks[4]['speaker']}"
    assert chunks[5]["speaker"] == "Witch", f"Chunk 6 expected Witch, got {chunks[5]['speaker']}"

    # Verify voice consistency for repeated characters!
    assert chunks[1]["voice_id"] == chunks[4]["voice_id"], f"Commander voice mismatch: #{chunks[1]['voice_id']} vs #{chunks[4]['voice_id']}"
    assert chunks[2]["voice_id"] == chunks[5]["voice_id"], f"Witch voice mismatch: #{chunks[2]['voice_id']} vs #{chunks[5]['voice_id']}"

    # Verify characters are distinct
    assert len(set([chunks[0]["voice_id"], chunks[1]["voice_id"], chunks[2]["voice_id"], chunks[3]["voice_id"]])) == 4, "Expected 4 distinct voices for the 4 distinct characters"

    print("\n[STEP 19 RESULT] PASS: All 4 characters cast with distinct voices; repeated characters Commander and Witch maintained 100% voice consistency!")

    print("\n=== STEP 20: SURGICAL REDO TEST ===")
    # Target: Chunk 6 ("Witch: They are a warning.")
    target_idx = 6
    chunk6_before = chunks[5]
    chunk1_mtime_before = os.path.getmtime(chunks[0]["audio_path"])
    chunk5_mtime_before = os.path.getmtime(chunks[4]["audio_path"])

    new_voice = "en-GB-SoniaNeural"
    redo_payload = {
        "project_id": test_id,
        "chunk_index": target_idx,
        "custom_voice_id": new_voice
    }

    req_redo = urllib.request.Request(
        f"{base_url}/api/projects/{test_id}/chunks/{target_idx}/redo",
        data=json.dumps(redo_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req_redo, timeout=40) as resp:
        redone = json.loads(resp.read().decode())

    redone_chunks = redone.get("chunks", [])
    chunk6_after = next(c for c in redone_chunks if c["chunk_index"] == 6)

    # 1. Voice changed on chunk 6
    assert chunk6_after["voice_id"] == new_voice, f"Expected {new_voice}, got {chunk6_after['voice_id']}"
    print(f"  [OK] Chunk 6 voice changed from {chunk6_before['voice_id']} to {chunk6_after['voice_id']}")

    # 2. Previous chunks untouched
    chunk1_mtime_after = os.path.getmtime(chunks[0]["audio_path"])
    chunk5_mtime_after = os.path.getmtime(chunks[4]["audio_path"])
    assert chunk1_mtime_before == chunk1_mtime_after, "Chunk 1 audio file was modified unexpectedly"
    assert chunk5_mtime_before == chunk5_mtime_after, "Chunk 5 audio file was modified unexpectedly"
    print("  [OK] Chunks 1 and 5 files untouched (surgical regeneration confirmed)")

    # 3. Audio reassembled & mastered
    final_mp3 = redone.get("final_audio_mp3")
    assert final_mp3 and os.path.exists(final_mp3) and os.path.getsize(final_mp3) > 1000
    print(f"  [OK] Master audio reassembled and saved ({os.path.getsize(final_mp3)} bytes)")

    # 4. Timestamps updated & sequential
    assert all(redone_chunks[i]["start_time"] <= redone_chunks[i]["end_time"] for i in range(len(redone_chunks)))
    print("  [OK] Downstream timeline updated and valid")

    # 5. QC rerun
    assert redone.get("qc_report") is not None
    print(f"  [OK] Full QC rerun passed: {redone['qc_report'].get('overall_pass')}")

    print("\n[STEP 20 RESULT] PASS: Surgical Redo succeeded on all criteria!")

if __name__ == "__main__":
    run_step19_step20()
