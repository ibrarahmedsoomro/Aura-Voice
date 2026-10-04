import os
import re
from typing import Dict, Optional
from ..database.db import DatabaseManager

class PronunciationAgent:
    """
    Module 4 & 18: Pronunciation Intelligence
    Hierarchy:
    1. Project Overrides (Highest priority)
    2. User/Database Dictionary
    3. System Default Rules
    """

    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager()
        self.system_defaults: Dict[str, str] = {
            "Mosquito": "Moss-KEE-toe",
            "Shikarpur": "Shi-kar-pur",
            "Karachi": "Ka-raa-chee",
            "Lahore": "La-hore",
            "Aura": "Aw-ra",
            "WWII": "World War Two",
            "B-25": "B twenty-five"
        }

    def save_user_entry(self, word: str, replacement: str, language: str = "en"):
        self.db.set_pronunciation(word, replacement, language)

    def get_all_entries(self) -> Dict[str, str]:
        entries = dict(self.system_defaults)
        entries.update(self.db.get_pronunciations())
        return entries

    def apply_pronunciations(self, text: str, project_overrides: Optional[Dict[str, str]] = None) -> str:
        combined: Dict[str, str] = self.get_all_entries()
        if project_overrides:
            combined.update(project_overrides)

        processed = text
        for word, replacement in combined.items():
            pattern = rf'\b{re.escape(word)}\b'
            processed = re.sub(pattern, replacement, processed, flags=re.IGNORECASE)

        return processed
