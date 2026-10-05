import os
import sqlite3
import json
from typing import List, Dict, Optional, Any
from datetime import datetime

class DatabaseManager:
    """
    Module 28: SQLite Database Persistence Layer.
    Persists projects, project_characters, project_chunks, scenes, QC reports,
    audio assets, subtitle assets, pronunciation dictionary, and user preferences.
    Guarantees non-destructive schema migrations and state continuity across restarts.
    """

    def __init__(self, db_path: Optional[str] = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        storage_dir = os.path.join(base_dir, "storage")
        os.makedirs(storage_dir, exist_ok=True)
        self.db_path = db_path or os.path.join(storage_dir, "auravoice.db")
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Projects Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                title TEXT,
                raw_input TEXT,
                original_text TEXT,
                normalized_text TEXT,
                spoken_text TEXT,
                input_type TEXT DEFAULT 'text',
                language TEXT DEFAULT 'en',
                voice_id TEXT,
                voice_name TEXT,
                style TEXT DEFAULT 'Cinematic',
                emotion TEXT DEFAULT 'auto',
                status TEXT DEFAULT 'CREATED',
                progress_percentage INTEGER DEFAULT 0,
                current_step_description TEXT DEFAULT '',
                total_duration_seconds REAL DEFAULT 0.0,
                final_audio_mp3 TEXT,
                final_audio_wav TEXT,
                final_srt TEXT,
                final_vtt TEXT,
                final_timings_json TEXT,
                error_message TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """)

            # 2. Project Characters Table (Step 5, 7, 16)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_characters (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                character_id TEXT,
                speaker_name TEXT,
                voice_id TEXT,
                provider TEXT DEFAULT 'edge-tts',
                is_locked INTEGER DEFAULT 0,
                style TEXT DEFAULT 'Cinematic',
                confidence REAL DEFAULT 0.95,
                reason TEXT DEFAULT '',
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
            """)

            # 3. Project Chunks Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_chunks (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                chunk_index INTEGER,
                speaker TEXT,
                speaker_name TEXT,
                character_id TEXT,
                text TEXT,
                spoken_text TEXT,
                voice_id TEXT,
                provider TEXT DEFAULT 'edge-tts',
                scene_id TEXT,
                emotion TEXT,
                speed REAL,
                pitch TEXT,
                rate TEXT,
                pause_before_ms INTEGER,
                pause_after_ms INTEGER,
                audio_path TEXT,
                duration REAL,
                start_time REAL,
                end_time REAL,
                qc_status TEXT,
                qc_message TEXT,
                retry_count INTEGER DEFAULT 0,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
            """)

            # Non-destructive migrations for chunks table
            columns_to_ensure = [
                ("speaker", "TEXT"),
                ("speaker_name", "TEXT"),
                ("character_id", "TEXT"),
                ("provider", "TEXT DEFAULT 'edge-tts'"),
                ("scene_id", "TEXT")
            ]
            for col_name, col_type in columns_to_ensure:
                try:
                    cursor.execute(f"ALTER TABLE project_chunks ADD COLUMN {col_name} {col_type}")
                except Exception:
                    pass

            # 4. Scenes Table (Step 10, 16)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS scenes (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                scene_index INTEGER,
                scene_name TEXT,
                location TEXT,
                time_of_day TEXT,
                mood TEXT,
                dramatic_intensity REAL DEFAULT 0.5,
                created_at TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
            """)

            # 5. QC Reports Table (Step 12, 16)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS qc_reports (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                overall_pass INTEGER,
                text_accuracy_score REAL,
                audio_integrity_score REAL,
                detected_clipping INTEGER,
                detected_silence INTEGER,
                failed_chunk_indices TEXT,
                repair_suggestions TEXT,
                details TEXT,
                created_at TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
            """)

            # 6. Pronunciation Dictionary Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS pronunciation_entries (
                word TEXT PRIMARY KEY,
                replacement TEXT,
                language TEXT DEFAULT 'en',
                created_at TEXT
            )
            """)

            # 7. User Preferences Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """)

            # Default initial pronunciations if table is empty
            cursor.execute("SELECT COUNT(*) FROM pronunciation_entries")
            if cursor.fetchone()[0] == 0:
                defaults = [
                    ("Mosquito", "Moss-KEE-toe", "en"),
                    ("WWII", "World War Two", "en"),
                    ("B-25", "B twenty-five", "en")
                ]
                now = datetime.now().isoformat()
                for w, r, l in defaults:
                    cursor.execute(
                        "INSERT OR IGNORE INTO pronunciation_entries (word, replacement, language, created_at) VALUES (?, ?, ?, ?)",
                        (w, r, l, now)
                    )

            conn.commit()

    # --- Project CRUD ---
    def save_project(self, project_data: Dict[str, Any]):
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO projects (
                id, title, raw_input, original_text, normalized_text, spoken_text,
                input_type, language, voice_id, voice_name, style, emotion,
                status, progress_percentage, current_step_description, total_duration_seconds,
                final_audio_mp3, final_audio_wav, final_srt, final_vtt, final_timings_json,
                error_message, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                project_data.get("id"),
                project_data.get("title", "Untitled Project"),
                project_data.get("raw_input", ""),
                project_data.get("original_text", project_data.get("raw_input", "")),
                project_data.get("normalized_text", ""),
                project_data.get("spoken_text", ""),
                project_data.get("input_type", "text"),
                project_data.get("language", "en"),
                project_data.get("voice_id", ""),
                project_data.get("voice_name", ""),
                project_data.get("style", "Cinematic"),
                project_data.get("emotion", "auto"),
                project_data.get("status", "CREATED"),
                project_data.get("progress_percentage", 0),
                project_data.get("current_step_description", ""),
                project_data.get("total_duration_seconds", 0.0),
                project_data.get("final_audio_mp3"),
                project_data.get("final_audio_wav"),
                project_data.get("final_srt"),
                project_data.get("final_vtt"),
                project_data.get("final_timings_json"),
                project_data.get("error_message"),
                project_data.get("created_at", now),
                now
            ))
            conn.commit()

    def update_project_status(self, project_id: str, status: str, progress: int, description: str, error: Optional[str] = None):
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE projects
            SET status = ?, progress_percentage = ?, current_step_description = ?, error_message = ?, updated_at = ?
            WHERE id = ?
            """, (status, progress, description, error, now, project_id))
            conn.commit()

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            row = cursor.fetchone()
            if not row:
                return None
            proj = dict(row)
            
            # Fetch chunks
            cursor.execute("SELECT * FROM project_chunks WHERE project_id = ? ORDER BY chunk_index ASC", (project_id,))
            proj["chunks"] = [dict(c) for c in cursor.fetchall()]

            # Fetch characters
            cursor.execute("SELECT * FROM project_characters WHERE project_id = ? ORDER BY speaker_name ASC", (project_id,))
            proj["characters"] = [dict(c) for c in cursor.fetchall()]

            # Fetch scenes
            cursor.execute("SELECT * FROM scenes WHERE project_id = ? ORDER BY scene_index ASC", (project_id,))
            proj["scenes"] = [dict(s) for s in cursor.fetchall()]

            # Fetch latest QC report
            cursor.execute("SELECT * FROM qc_reports WHERE project_id = ? ORDER BY created_at DESC LIMIT 1", (project_id,))
            qc_row = cursor.fetchone()
            if qc_row:
                qcd = dict(qc_row)
                try:
                    qcd["failed_chunk_indices"] = json.loads(qcd.get("failed_chunk_indices") or "[]")
                    qcd["repair_suggestions"] = json.loads(qcd.get("repair_suggestions") or "{}")
                    qcd["details"] = json.loads(qcd.get("details") or "{}")
                except Exception:
                    pass
                proj["qc_report"] = qcd
            else:
                proj["qc_report"] = None

            return proj

    def list_projects(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects ORDER BY updated_at DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def delete_project(self, project_id: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM project_chunks WHERE project_id = ?", (project_id,))
            cursor.execute("DELETE FROM project_characters WHERE project_id = ?", (project_id,))
            cursor.execute("DELETE FROM scenes WHERE project_id = ?", (project_id,))
            cursor.execute("DELETE FROM qc_reports WHERE project_id = ?", (project_id,))
            cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            conn.commit()

    # --- Chunks CRUD ---
    def save_chunk(self, chunk_data: Dict[str, Any]):
        chunk_id = f"{chunk_data['project_id']}_{chunk_data['chunk_index']}"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            spk = chunk_data.get("speaker") or chunk_data.get("speaker_name")
            cursor.execute("""
            INSERT OR REPLACE INTO project_chunks (
                id, project_id, chunk_index, speaker, speaker_name, character_id,
                text, spoken_text, voice_id, provider, scene_id, emotion,
                speed, pitch, rate, pause_before_ms, pause_after_ms,
                audio_path, duration, start_time, end_time, qc_status, qc_message, retry_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                chunk_id,
                chunk_data["project_id"],
                chunk_data["chunk_index"],
                spk,
                spk,
                chunk_data.get("character_id") or (spk.lower() if spk else None),
                chunk_data["text"],
                chunk_data.get("spoken_text", chunk_data["text"]),
                chunk_data.get("voice_id", ""),
                chunk_data.get("provider", "edge-tts"),
                chunk_data.get("scene_id"),
                chunk_data.get("emotion", "neutral"),
                chunk_data.get("speed", 1.0),
                chunk_data.get("pitch", "+0Hz"),
                chunk_data.get("rate", "+0%"),
                chunk_data.get("pause_before_ms", 150),
                chunk_data.get("pause_after_ms", 350),
                chunk_data.get("audio_path") or chunk_data.get("audio_file"),
                chunk_data.get("duration", 0.0),
                chunk_data.get("start_time", 0.0),
                chunk_data.get("end_time", 0.0),
                chunk_data.get("qc_status", "PENDING"),
                chunk_data.get("qc_message", ""),
                chunk_data.get("retry_count", 0)
            ))
            conn.commit()

    # --- Character Voice Management (Step 5, 7, 16) ---
    def save_characters(self, project_id: str, characters: List[Dict[str, Any]]):
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for ch in characters:
                cid = ch.get("character_id") or ch.get("speaker_name", "").lower()
                pk = f"{project_id}_{cid}"
                cursor.execute("""
                INSERT OR REPLACE INTO project_characters (
                    id, project_id, character_id, speaker_name, voice_id, provider,
                    is_locked, style, confidence, reason, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pk,
                    project_id,
                    cid,
                    ch.get("speaker_name", cid.capitalize()),
                    ch.get("voice_id", ""),
                    ch.get("provider", "edge-tts"),
                    1 if ch.get("is_locked") else 0,
                    ch.get("style", "Cinematic"),
                    ch.get("confidence", 0.95),
                    ch.get("reason", "Auto-cast profile match"),
                    now,
                    now
                ))
            conn.commit()

    def get_project_characters(self, project_id: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM project_characters WHERE project_id = ?", (project_id,))
            return [dict(r) for r in cursor.fetchall()]

    def update_character_voice(self, project_id: str, character_id: str, voice_id: str, is_locked: Optional[bool] = None):
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if is_locked is not None:
                cursor.execute("""
                UPDATE project_characters
                SET voice_id = ?, is_locked = ?, updated_at = ?
                WHERE project_id = ? AND character_id = ?
                """, (voice_id, 1 if is_locked else 0, now, project_id, character_id.lower()))
            else:
                cursor.execute("""
                UPDATE project_characters
                SET voice_id = ?, updated_at = ?
                WHERE project_id = ? AND character_id = ?
                """, (voice_id, now, project_id, character_id.lower()))
            conn.commit()

    # --- Scene Management (Step 10, 16) ---
    def save_scenes(self, project_id: str, scenes: List[Dict[str, Any]]):
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM scenes WHERE project_id = ?", (project_id,))
            for sc in scenes:
                sid = f"{project_id}_{sc.get('scene_index', 1)}"
                cursor.execute("""
                INSERT INTO scenes (
                    id, project_id, scene_index, scene_name, location, time_of_day, mood, dramatic_intensity, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sid,
                    project_id,
                    sc.get("scene_index", 1),
                    sc.get("scene_name", "Scene 1"),
                    sc.get("location", "Unknown"),
                    sc.get("time_of_day", "Any"),
                    sc.get("mood", "neutral"),
                    sc.get("dramatic_intensity", 0.5),
                    now
                ))
            conn.commit()

    def get_project_scenes(self, project_id: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM scenes WHERE project_id = ? ORDER BY scene_index ASC", (project_id,))
            return [dict(r) for r in cursor.fetchall()]

    # --- QC Reports CRUD (Step 12, 16) ---
    def save_qc_report(self, project_id: str, report_data: Dict[str, Any]):
        now = datetime.now().isoformat()
        rid = f"QC-{project_id}-{int(datetime.now().timestamp())}"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO qc_reports (
                id, project_id, overall_pass, text_accuracy_score, audio_integrity_score,
                detected_clipping, detected_silence, failed_chunk_indices, repair_suggestions, details, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rid,
                project_id,
                1 if report_data.get("overall_pass") else 0,
                report_data.get("text_accuracy_score", 1.0),
                report_data.get("audio_integrity_score", 1.0),
                1 if report_data.get("detected_clipping") else 0,
                1 if report_data.get("detected_unnatural_silence") else 0,
                json.dumps(report_data.get("failed_chunk_indices", [])),
                json.dumps(report_data.get("repair_suggestions", {})),
                json.dumps(report_data.get("details", {})),
                now
            ))
            conn.commit()

    # --- Pronunciation Dictionary ---
    def get_pronunciations(self) -> Dict[str, str]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT word, replacement FROM pronunciation_entries")
            return {row["word"]: row["replacement"] for row in cursor.fetchall()}

    def set_pronunciation(self, word: str, replacement: str, language: str = "en"):
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO pronunciation_entries (word, replacement, language, created_at)
            VALUES (?, ?, ?, ?)
            """, (word, replacement, language, now))
            conn.commit()

    def delete_pronunciation(self, word: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM pronunciation_entries WHERE word = ?", (word,))
            conn.commit()

    # --- User Preferences ---
    def get_preference(self, key: str, default: Any = None) -> Any:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM user_preferences WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                try:
                    return json.loads(row["value"])
                except Exception:
                    return row["value"]
            return default

    def set_preference(self, key: str, value: Any):
        val_str = json.dumps(value) if not isinstance(value, str) else value
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO user_preferences (key, value) VALUES (?, ?)", (key, val_str))
            conn.commit()
