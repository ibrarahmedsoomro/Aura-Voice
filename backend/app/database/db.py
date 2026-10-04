import os
import sqlite3
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

class DatabaseManager:
    """
    Relational SQLite persistence for Aura Voice.
    Stores Projects, Chunks, QC Reports, Pronunciation Dictionary, and User Preferences.
    Ensures zero state loss across backend restarts.
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
            
            # Projects Table
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

            # Project Chunks Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_chunks (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                chunk_index INTEGER,
                text TEXT,
                spoken_text TEXT,
                voice_id TEXT,
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

            # Pronunciation Dictionary Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS pronunciation_entries (
                word TEXT PRIMARY KEY,
                replacement TEXT,
                language TEXT DEFAULT 'en',
                created_at TEXT
            )
            """)

            # User Preferences Table
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
                    ("Shikarpur", "Shi-kar-pur", "ur"),
                    ("Karachi", "Ka-raa-chee", "ur"),
                    ("Lahore", "La-hore", "ur"),
                    ("Aura", "Aw-ra", "en"),
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
            return proj

    def list_projects(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects ORDER BY updated_at DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def save_chunk(self, chunk_data: Dict[str, Any]):
        chunk_id = f"{chunk_data['project_id']}_{chunk_data['chunk_index']}"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO project_chunks (
                id, project_id, chunk_index, text, spoken_text, voice_id,
                emotion, speed, pitch, rate, pause_before_ms, pause_after_ms,
                audio_path, duration, start_time, end_time, qc_status, qc_message, retry_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                chunk_id,
                chunk_data["project_id"],
                chunk_data["chunk_index"],
                chunk_data["text"],
                chunk_data.get("spoken_text", chunk_data["text"]),
                chunk_data.get("voice_id", ""),
                chunk_data.get("emotion", "neutral"),
                chunk_data.get("speed", 1.0),
                chunk_data.get("pitch", "+0Hz"),
                chunk_data.get("rate", "+0%"),
                chunk_data.get("pause_before_ms", 150),
                chunk_data.get("pause_after_ms", 350),
                chunk_data.get("audio_path"),
                chunk_data.get("duration", 0.0),
                chunk_data.get("start_time", 0.0),
                chunk_data.get("end_time", 0.0),
                chunk_data.get("qc_status", "PENDING"),
                chunk_data.get("qc_message", ""),
                chunk_data.get("retry_count", 0)
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
