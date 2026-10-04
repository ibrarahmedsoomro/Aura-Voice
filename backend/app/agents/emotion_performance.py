import re
from typing import Dict, List, Any

class EmotionPerformanceAgent:
    """
    Module 3: Emotion & Performance Agent
    Classifies sentence-level dramatic intent, speed, pitch,
    pause timings, and emphasized/stress words.
    """

    def __init__(self):
        self.emotion_lexicons = {
            "horror": ["blood", "monster", "shadow", "creature", "death", "grave", "corpse", "demon", "scream", "evil", "haunted"],
            "suspense": ["slowly", "whisper", "silent", "creak", "darkness", "suddenly", "footsteps", "waiting", "hiding", "vanished", "trap", "danger"],
            "excited": ["incredible", "astonishing", "breakthrough", "victory", "triumph", "unbelievable", "amazing", "finally", "celebrate", "huge"],
            "sad": ["cried", "grief", "lost", "mourn", "tears", "hopeless", "tragedy", "broken", "alone", "goodbye"],
            "dramatic": ["war", "battle", "fate", "history", "destiny", "explosion", "doomed", "collapse", "clash", "storm", "end of days"]
        }

    def analyze_sentence_performance(self, sentence: str, global_emotion_override: str = "auto") -> Dict[str, Any]:
        """
        Determines emotion, intensity, rate, pitch, and natural pause metrics.
        """
        lower = sentence.lower()
        detected_emotion = "narration"
        intensity = 0.5

        if global_emotion_override != "auto" and global_emotion_override:
            detected_emotion = global_emotion_override
        else:
            # Score against lexicons
            scores: Dict[str, int] = {}
            for emo, keywords in self.emotion_lexicons.items():
                match_count = sum(1 for kw in keywords if re.search(rf'\b{re.escape(kw)}\b', lower))
                if match_count > 0:
                    scores[emo] = match_count
                    
            if scores:
                detected_emotion = max(scores, key=scores.get)
                intensity = min(0.9, 0.5 + (scores[detected_emotion] * 0.15))

        # Prosody mapping for TTS Engines (Edge-TTS Rate and Pitch syntax)
        rate = "+0%"
        pitch = "+0Hz"
        pause_before_ms = 150
        pause_after_ms = 350
        speed_factor = 1.0

        if detected_emotion == "suspense":
            rate = "-8%"
            pitch = "-2Hz"
            pause_before_ms = 300
            pause_after_ms = 600
            speed_factor = 0.92
        elif detected_emotion == "horror":
            rate = "-12%"
            pitch = "-4Hz"
            pause_before_ms = 400
            pause_after_ms = 750
            speed_factor = 0.88
        elif detected_emotion == "whisper":
            rate = "-15%"
            pitch = "-3Hz"
            pause_before_ms = 350
            pause_after_ms = 650
            speed_factor = 0.85
        elif detected_emotion == "excited":
            rate = "+8%"
            pitch = "+3Hz"
            pause_before_ms = 100
            pause_after_ms = 250
            speed_factor = 1.08
        elif detected_emotion == "dramatic":
            rate = "-5%"
            pitch = "-2Hz"
            pause_before_ms = 250
            pause_after_ms = 500
            speed_factor = 0.95
        elif detected_emotion == "sad":
            rate = "-8%"
            pitch = "-1Hz"
            pause_before_ms = 250
            pause_after_ms = 550
            speed_factor = 0.92

        # Identify punchy stress words
        words = re.findall(r'\b[A-Za-z0-9_-]+\b', sentence)
        stress_words = []
        for w in words:
            if len(w) > 5 and w.lower() in lower:
                stress_words.append(w)
        stress_words = stress_words[:3]

        return {
            "emotion": detected_emotion,
            "intensity": intensity,
            "rate": rate,
            "pitch": pitch,
            "speed": speed_factor,
            "pause_before_ms": pause_before_ms,
            "pause_after_ms": pause_after_ms,
            "stress_words": stress_words
        }
