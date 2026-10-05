import urllib.request
import json

payload = {
    "text": "Narrator: The old castle gates swung open with a screech.\nCommander: Keep your shields raised!\nWitch: You fools! None shall leave alive.",
    "voice_id": "auto",
    "style_preference": "Cinematic",
    "emotion_mode": "auto",
    "language_hint": "en"
}

req = urllib.request.Request(
    "http://localhost:8001/api/projects/TEST-MULTI-VOICES/generate",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
        print(f"[STATUS] {data.get('status')}")
        print(f"[CHUNKS] Total: {len(data.get('chunks', []))}")
        for c in data.get("chunks", []):
            spk = c.get("speaker") or "None"
            v_id = c.get("voice_id") or "None"
            print(f"  Chunk #{c['chunk_index']}: [{spk}] Voice: {v_id} -> \"{c['text']}\"")
        print(f"[AUDIO] Final MP3: {data.get('final_audio_mp3')}")
except Exception as e:
    print(f"[ERROR] {e}")
