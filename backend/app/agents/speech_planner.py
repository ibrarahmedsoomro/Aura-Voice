import re
from typing import List, Dict, Optional
from ..models.schemas import ChunkPlan
from .emotion_performance import EmotionPerformanceAgent
from .pronunciation import PronunciationAgent

class SpeechPlannerAgent:
    """
    Module 8: Speech Planner Agent
    Splits normalized text into natural breath/clause chunks and attaches prosody metadata.
    """

    def __init__(self, emotion_agent: EmotionPerformanceAgent, pronunciation_agent: PronunciationAgent):
        self.emotion_agent = emotion_agent
        self.pronunciation_agent = pronunciation_agent

    def plan_speech(
        self,
        normalized_text: str,
        emotion_mode: str = "auto",
        custom_pronunciations: Optional[Dict[str, str]] = None
    ) -> List[ChunkPlan]:
        """
        Splits text on sentences and clause punctuation (. , ! ? ; : —).
        Prevents unnaturally long single bursts.
        """
        # Split on sentence boundaries, keeping punctuation
        raw_sentences = re.split(r'(?<=[.!?…])\s+', normalized_text)
        
        chunks: List[ChunkPlan] = []
        chunk_idx = 1

        for raw_s in raw_sentences:
            s = raw_s.strip()
            if not s:
                continue

            # If sentence is extremely long (>200 chars or >30 words), split by comma or semi-colon
            sub_clauses = [s]
            if len(s.split()) > 25 and (',' in s or ';' in s or '—' in s):
                sub_clauses = [c.strip() for c in re.split(r'(?<=[,;—])\s+', s) if c.strip()]

            for clause in sub_clauses:
                # Apply pronunciation overrides
                spoken_form = self.pronunciation_agent.apply_pronunciations(clause, custom_pronunciations)

                # Determine emotion and prosody
                performance = self.emotion_agent.analyze_sentence_performance(clause, emotion_mode)

                plan = ChunkPlan(
                    chunk_index=chunk_idx,
                    text=clause,
                    normalized_text=spoken_form,
                    emotion=performance["emotion"],
                    speed=performance["speed"],
                    pitch=performance["pitch"],
                    rate=performance["rate"],
                    pause_before_ms=performance["pause_before_ms"],
                    pause_after_ms=performance["pause_after_ms"],
                    stress_words=performance["stress_words"]
                )
                chunks.append(plan)
                chunk_idx += 1

        return chunks
