# Aura Voice (VOXAGENT)
### Autonomous AI Voice Agent with Quality Control, Prosody Intelligence & Surgical Repair

Aura Voice is an agentic AI voice system designed from the ground up for high-fidelity narrations, audiobooks, documentaries, and social media voiceovers. Unlike ordinary Text-to-Speech tools, Aura Voice executes an autonomous lifecycle:
**Understand → Plan → Choose → Synthesize → Listen/Analyze (QC) → Repair (Targeted) → Master → Deliver.**

---

## Key Features

1. **Autonomous Quality Control (QC Agent)**
   - Multi-layer verification: speech cadence, silence bounds, audio signal integrity, and duration-to-word sanity.
   - Certifies all speech chunks before delivery.

2. **Line-by-Line Redo & Surgical Repair (Module 27 & 15)**
   - When a specific sentence needs tuning, **only that chunk is regenerated**. The rest of your 3-minute narration remains untouched.
   - Adjust pronunciations, speed, or emotion per line.

3. **Multi-Lingual & Code-Switching Intelligence (Module 2)**
   - Built-in support for **English**, **Urdu (اردو)**, **Hindi**, and **Roman Urdu / Hinglish**.
   - Automatic spoken normalization for historical dates (e.g. `1944` → `nineteen forty-four`), military acronyms (`WWII` → `World War Two`, `B-25` → `B twenty-five`), percentages, and currencies.

4. **Consent & Voice Safety Gate (Module 7)**
   - Hard policy enforcement: blocks unauthorized celebrity voice cloning.
   - Routes requests to premium licensed neural voices and authorized style equivalents.

5. **Audio Post-Processing & Mastering (Module 11 & 12)**
   - Built-in **FFmpeg EBU R128 Loudness Normalization** (-14 LUFS target).
   - High-pass de-rumble filter and dynamic range compression.

6. **Complete Subtitle & Timing Engine (Module 13 & 17)**
   - Automatic generation of synchronized **SRT**, **VTT**, and **JSON** timecodes ready for CapCut, Premiere Pro, or DaVinci Resolve.

7. **ChatGPT / Claude Inspired Minimalist UI**
   - Clean, distraction-free workspace with dark mode, project history sidebar, waveform scrubbing player, and interactive chunk studio.

---

## Project Structure

```
Aura Voice/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   └── voice_catalog.py      # Licensed voice catalog & consent safety gate
│   │   ├── models/
│   │   │   └── schemas.py            # Pydantic data schemas
│   │   ├── agents/
│   │   │   ├── script_intelligence.py # Language detection & number/date normalization
│   │   │   ├── emotion_performance.py # Sentence-level emotion & prosody planning
│   │   │   ├── pronunciation.py       # Multi-tiered phonetic dictionary
│   │   │   ├── speech_planner.py      # Natural breath & clause chunking
│   │   │   ├── audio_processor.py     # FFmpeg mastering, EBU R128 & concat
│   │   │   ├── timing_alignment.py    # Subtitle, SRT, VTT & JSON timing engine
│   │   │   ├── qc_agent.py            # Autonomous QC & signal verification
│   │   │   ├── repair_agent.py        # Surgical chunk regeneration & retry strategies
│   │   │   └── memory_agent.py        # Project history & voice preference learning
│   │   ├── providers/
│   │   │   ├── base.py                # Abstract TTS provider interface
│   │   │   └── edge_provider.py       # High-fidelity Edge neural TTS adapter
│   │   ├── orchestrator/
│   │   │   └── central_orchestrator.py # Central state machine & agent workflow
│   │   └── api/
│   │       └── routes.py              # REST API & WebSocket endpoints
│   ├── exports/                       # Master WAV, MP3, SRT, VTT, JSON
│   ├── storage/                       # Chunks, memory & pronunciation dicts
│   ├── requirements.txt
│   └── main.py                        # FastAPI application entrypoint
│
├── frontend/                          # Vite + React + TypeScript + Tailwind CSS
│   ├── src/
│   │   ├── App.tsx                    # ChatGPT/Claude style UI & audio player
│   │   ├── main.tsx
│   │   └── index.css
│   └── package.json
│
├── start.bat                          # One-click Windows starter
└── README.md
```

---

## Quickstart

### 1. Launch with One Click
Double click [`start.bat`](start.bat) in the root folder. It will launch both the backend and frontend simultaneously.

### 2. Or Run Manually

**Start Backend:**
```powershell
cd backend
.\.venv\Scripts\python.exe main.py
```
Backend API will be live at `http://localhost:8000` (docs at `http://localhost:8000/docs`).

**Start Frontend:**
```powershell
cd frontend
npm run dev
```
Frontend UI will be live at `http://localhost:3000`.

---

## Export Outputs

Every narration project produces:
- `*_final.mp3`: 320 kbps mastered audio
- `*_final.wav`: 44.1 kHz 16-bit PCM master
- `*_subtitles.srt`: SubRip captions
- `*_subtitles.vtt`: WebVTT captions
- `*_timings.json`: Exact chunk timecodes for video editing
