import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

class ProjectMemoryAgent:
    """
    Module 19 & 20: Project Memory & Learning Feedback Engine
    Saves and indexes project history, user preferences, and voice success metrics.
    """

    def __init__(self, memory_dir: Optional[str] = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.memory_dir = memory_dir or os.path.join(base_dir, "storage", "memory")
        self.user_prefs_file = os.path.join(self.memory_dir, "user_preferences.json")
        self.history_file = os.path.join(self.memory_dir, "projects_history.json")
        self.voice_stats_file = os.path.join(self.memory_dir, "voice_learning_stats.json")
        os.makedirs(self.memory_dir, exist_ok=True)

    def _read_json(self, path: str, default: Any) -> Any:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return default
        return default

    def _write_json(self, path: str, data: Any):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_user_preferences(self) -> Dict[str, Any]:
        return self._read_json(self.user_prefs_file, {
            "preferred_voice_id": "vox-cinematic-male",
            "preferred_style": "Cinematic",
            "default_emotion": "auto",
            "mastering_enabled": True
        })

    def save_user_preferences(self, prefs: Dict[str, Any]):
        current = self.get_user_preferences()
        current.update(prefs)
        self._write_json(self.user_prefs_file, current)

    def record_project_completion(self, project_id: str, title: str, voice_id: str, duration: float, qc_pass: bool):
        history: List[Dict[str, Any]] = self._read_json(self.history_file, [])
        record = {
            "project_id": project_id,
            "title": title,
            "voice_id": voice_id,
            "duration": round(duration, 2),
            "qc_pass": qc_pass,
            "timestamp": datetime.now().isoformat()
        }
        # Prepend to history
        history.insert(0, record)
        history = history[:100] # keep last 100
        self._write_json(self.history_file, history)

        # Update voice learning score
        stats: Dict[str, Dict[str, Any]] = self._read_json(self.voice_stats_file, {})
        v_stat = stats.get(voice_id, {"uses": 0, "qc_successes": 0, "confidence": 0.95})
        v_stat["uses"] += 1
        if qc_pass:
            v_stat["qc_successes"] += 1
        v_stat["confidence"] = round(v_stat["qc_successes"] / v_stat["uses"], 3)
        stats[voice_id] = v_stat
        self._write_json(self.voice_stats_file, stats)

    def get_history(self) -> List[Dict[str, Any]]:
        return self._read_json(self.history_file, [])
