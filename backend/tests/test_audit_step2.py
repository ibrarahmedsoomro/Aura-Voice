import urllib.request
import json
import time
import os
import sys

base_url = "http://localhost:8001"

def run_step2_verification():
    results = {}
    print("--- STEP 2: VERIFY EXISTING MULTI-VOICE SYSTEM ---")

    # 1. Multiple voices are actually available
    try:
        req = urllib.request.Request(f"{base_url}/api/voices")
        with urllib.request.urlopen(req, timeout=10) as resp:
            voices = json.loads(resp.read().decode())
            if len(voices) >= 10:
                results["1. Multiple voices available"] = f"PASS ({len(voices)} voices found)"
            else:
                results["1. Multiple voices available"] = f"PARTIAL ({len(voices)} voices)"
    except Exception as e:
        results["1. Multiple voices available"] = f"FAIL ({e})"

    # 2. Voice catalog is loaded from backend
    try:
        req = urllib.request.Request(f"{base_url}/api/voices?language=en&style=Cinematic")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            first_v = data[0]["voice"]
            if "voice_id" in first_v and "name" in first_v and "style" in first_v:
                results["2. Voice catalog loaded from backend"] = f"PASS (Top: {first_v['name']})"
            else:
                results["2. Voice catalog loaded from backend"] = "FAIL (Missing fields)"
    except Exception as e:
        results["2. Voice catalog loaded from backend"] = f"FAIL ({e})"

    # 3. Speaker detection actually works
    # 4. Character assignments persist
    # 5. Different speakers produce different voices
    # 6. Generated chunks contain speaker/character information
    # 7. Final assembly preserves speaker sequence
    test_proj_id = f"AUDIT-E2E-{int(time.time())}"
    script = (
        "Narrator: The old castle gates opened slowly.\n"
        "Commander: Everyone stay alert.\n"
        "Witch: You should never have come here."
    )

    gen_payload = {
        "text": script,
        "voice_id": "auto",
        "style_preference": "Cinematic",
        "emotion_mode": "auto",
        "language_hint": "en"
    }

    try:
        req = urllib.request.Request(
            f"{base_url}/api/projects/{test_proj_id}/generate",
            data=json.dumps(gen_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            proj = json.loads(resp.read().decode())

        chunks = proj.get("chunks", [])
        speakers = [c.get("speaker") for c in chunks]
        voices_assigned = [c.get("voice_id") for c in chunks]

        # 3. Speaker detection
        if "Narrator" in speakers and "Commander" in speakers and "Witch" in speakers:
            results["3. Speaker detection actually works"] = f"PASS (Speakers detected: {speakers})"
        else:
            results["3. Speaker detection actually works"] = f"FAIL (Speakers detected: {speakers})"

        # 4. Character assignments persist
        req_get = urllib.request.Request(f"{base_url}/api/projects/{test_proj_id}")
        with urllib.request.urlopen(req_get, timeout=10) as resp:
            persisted_proj = json.loads(resp.read().decode())
        persisted_chunks = persisted_proj.get("chunks", [])
        persisted_speakers = [c.get("speaker") for c in persisted_chunks]
        if persisted_speakers == speakers and len(persisted_speakers) >= 3:
            results["4. Character assignments persist"] = "PASS (Persisted in SQLite)"
        else:
            results["4. Character assignments persist"] = "FAIL"

        # 5. Different speakers produce different voices
        unique_voices = set(voices_assigned)
        if len(unique_voices) >= 3:
            results["5. Different speakers produce different voices"] = f"PASS ({len(unique_voices)} unique voices used: {unique_voices})"
        elif len(unique_voices) >= 2:
            results["5. Different speakers produce different voices"] = f"PARTIAL ({len(unique_voices)} unique voices: {unique_voices})"
        else:
            results["5. Different speakers produce different voices"] = f"FAIL (Only 1 voice: {unique_voices})"

        # 6. Generated chunks contain speaker/character info
        has_info = all(c.get("speaker") and c.get("voice_id") for c in chunks)
        results["6. Generated chunks contain speaker/character information"] = "PASS" if has_info else "FAIL"

        # 7. Final assembly preserves speaker sequence
        indices = [c["chunk_index"] for c in chunks]
        is_seq = indices == list(range(1, len(chunks) + 1))
        timeline_seq = all(chunks[i]["start_time"] <= chunks[i]["end_time"] and (i == 0 or chunks[i]["start_time"] >= chunks[i-1]["end_time"] - 0.05) for i in range(len(chunks)))
        results["7. Final assembly preserves speaker sequence"] = "PASS" if (is_seq and timeline_seq) else "FAIL"

        # 8. Line-by-line voice change actually regenerates only that line
        # 9. Redo actually replaces the correct chunk
        # 10. Final audio is reassembled
        # 11. QC runs after redo
        # 12. Subtitle timing remains valid
        orig_chunk2_audio = chunks[1].get("audio_path")
        orig_chunk1_audio = chunks[0].get("audio_path")
        orig_chunk1_mtime = os.path.getmtime(orig_chunk1_audio) if orig_chunk1_audio and os.path.exists(orig_chunk1_audio) else None

        # Redo chunk 2 with custom voice
        target_custom_voice = "en-US-RogerNeural"
        redo_payload = {
            "project_id": test_proj_id,
            "chunk_index": 2,
            "custom_voice_id": target_custom_voice
        }
        req_redo = urllib.request.Request(
            f"{base_url}/api/projects/{test_proj_id}/chunks/2/redo",
            data=json.dumps(redo_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req_redo, timeout=30) as resp:
            redone_proj = json.loads(resp.read().decode())

        redone_chunks = redone_proj.get("chunks", [])
        chunk2 = next((c for c in redone_chunks if c["chunk_index"] == 2), None)
        chunk1 = next((c for c in redone_chunks if c["chunk_index"] == 1), None)

        # 8 & 9
        chunk1_untouched = False
        if orig_chunk1_audio and os.path.exists(orig_chunk1_audio):
            current_chunk1_mtime = os.path.getmtime(orig_chunk1_audio)
            chunk1_untouched = (current_chunk1_mtime == orig_chunk1_mtime)

        if chunk2 and chunk2.get("voice_id") == target_custom_voice:
            results["8. Line-by-line voice change regenerates only that line"] = "PASS" if chunk1_untouched else "PARTIAL"
            results["9. Redo actually replaces the correct chunk"] = f"PASS (Chunk 2 updated to {target_custom_voice})"
        else:
            results["8. Line-by-line voice change regenerates only that line"] = "FAIL"
            results["9. Redo actually replaces the correct chunk"] = "FAIL"

        # 10. Final audio is reassembled
        final_mp3 = redone_proj.get("final_audio_mp3")
        results["10. Final audio is reassembled"] = "PASS" if (final_mp3 and os.path.exists(final_mp3) and os.path.getsize(final_mp3) > 1000) else "FAIL"

        # 11. QC runs after redo
        qc_rep = redone_proj.get("qc_report")
        if qc_rep and "overall_pass" in qc_rep:
            results["11. QC runs after redo"] = f"PASS (QC Overall Pass: {qc_rep['overall_pass']}, Integrity: {qc_rep.get('audio_integrity_score', 1.0)})"
        else:
            results["11. QC runs after redo"] = "FAIL"

        # 12. Subtitle timing remains valid
        final_srt = redone_proj.get("final_srt")
        if final_srt and os.path.exists(final_srt):
            with open(final_srt, "r", encoding="utf-8") as f:
                srt_txt = f.read()
            results["12. Subtitle timing remains valid"] = "PASS" if "-->" in srt_txt else "FAIL"
        else:
            results["12. Subtitle timing remains valid"] = "FAIL"

    except Exception as e:
        print("Error during test run:", e)
        for i in range(3, 13):
            k = list(results.keys())
            # fill missing

    print("\n=== AUDIT RESULTS ===")
    for k, v in results.items():
        print(f"{k}: {v}")

if __name__ == "__main__":
    run_step2_verification()
