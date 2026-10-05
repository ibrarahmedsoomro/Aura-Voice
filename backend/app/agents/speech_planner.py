import re
from typing import List, Dict, Optional, Tuple, Any
from ..models.schemas import ChunkPlan, ProjectCharacter, ScenePlan
from .emotion_performance import EmotionPerformanceAgent
from .pronunciation import PronunciationAgent
from ..core.voice_catalog import VOICE_CATALOG, find_voice_by_id_or_profile

class SpeechPlannerAgent:
    """
    Module 8 & Auto Cast 2.0:
    Intelligent Script, Scene, and Multi-Character Speech Planner.
    Supports dialogue-style scripts ('John:', '[Commander]', etc.),
    scene detection, character voice casting with consistency guarantees,
    and performance direction.
    """

    def __init__(self, emotion_agent: EmotionPerformanceAgent, pronunciation_agent: PronunciationAgent):
        self.emotion_agent = emotion_agent
        self.pronunciation_agent = pronunciation_agent

        # Speaker archetype voice heuristics with confidence and human-readable reasons
        self.archetypes = {
            "narrator": {
                "voice_id": "en-US-ChristopherNeural",
                "style": "Cinematic",
                "reason": "Deep, resonant cinematic baritone for foundational narration"
            },
            "commander": {
                "voice_id": "en-US-BrianMultilingualNeural",
                "style": "Dramatic",
                "reason": "Authoritative, commanding presence for military leaders and tactical dialogue"
            },
            "captain": {
                "voice_id": "en-US-BrianMultilingualNeural",
                "style": "Dramatic",
                "reason": "Resolute, commanding presence suited for a tactical officer"
            },
            "soldier": {
                "voice_id": "en-US-BrianMultilingualNeural",
                "style": "Dramatic",
                "reason": "Grounded and direct cadence for frontline personnel"
            },
            "villain": {
                "voice_id": "en-GB-RyanNeural",
                "style": "Cinematic",
                "reason": "Sinister, calculative British tone for primary antagonists"
            },
            "witch": {
                "voice_id": "en-US-AriaNeural",
                "style": "Dramatic",
                "reason": "High-tension, intense dramatic inflection for occult/sorceress characters"
            },
            "sorceress": {
                "voice_id": "en-US-AriaNeural",
                "style": "Dramatic",
                "reason": "Mystical, sharp dramatic enunciation"
            },
            "doctor": {
                "voice_id": "en-US-EmmaMultilingualNeural",
                "style": "Documentary",
                "reason": "Analytical, measured, highly articulate cadence for medical/science roles"
            },
            "scientist": {
                "voice_id": "en-US-GuyNeural",
                "style": "Documentary",
                "reason": "Inquisitive, credible explainer tone for research leads"
            },
            "elder": {
                "voice_id": "en-US-RogerNeural",
                "style": "Storyteller",
                "reason": "Warm, gravelly vintage timbre for wise mentors and elder figures"
            },
            "grandfather": {
                "voice_id": "en-US-RogerNeural",
                "style": "Storyteller",
                "reason": "Warm, resonant nostalgic tone for paternal/grandfatherly roles"
            },
            "queen": {
                "voice_id": "en-GB-SoniaNeural",
                "style": "Dramatic",
                "reason": "Poised, regal British delivery for nobility and royalty"
            },
            "princess": {
                "voice_id": "en-GB-SoniaNeural",
                "style": "Dramatic",
                "reason": "Aristocratic, elegant cadence"
            },
            "girl": {
                "voice_id": "en-US-AnaNeural",
                "style": "Conversational",
                "reason": "Playful, energetic youthful female voice"
            },
            "child": {
                "voice_id": "en-US-AnaNeural",
                "style": "Conversational",
                "reason": "Youthful, expressive cadence"
            },
            "creator": {
                "voice_id": "en-US-EricNeural",
                "style": "Conversational",
                "reason": "Fast, modern, dynamic creator tone for podcasts and social media"
            }
        }

        # Available voice pool for diverse character casting
        self.male_voice_pool = [
            ("en-US-BrianMultilingualNeural", "Dramatic", "Authoritative action lead"),
            ("en-GB-RyanNeural", "Cinematic", "Aristocratic British dramatic male"),
            ("en-US-GuyNeural", "Documentary", "Credible, calm analytical male"),
            ("en-US-AndrewMultilingualNeural", "Conversational", "Warm, modern conversational male"),
            ("en-US-RogerNeural", "Storyteller", "Wise, mature resonant male"),
            ("en-GB-ThomasNeural", "Documentary", "Refined classical Victorian male"),
            ("en-US-EricNeural", "Conversational", "Vibrant, youthful male")
        ]

        self.female_voice_pool = [
            ("en-US-JennyNeural", "Storyteller", "Expressive, versatile female lead"),
            ("en-US-AriaNeural", "Dramatic", "Dynamic, high-intensity dramatic female"),
            ("en-US-EmmaMultilingualNeural", "Documentary", "Professional, measured authoritative female"),
            ("en-GB-SoniaNeural", "Dramatic", "Poised, regal British female"),
            ("en-US-AvaMultilingualNeural", "Storyteller", "Intimate, gentle melancholic female"),
            ("en-US-AnaNeural", "Conversational", "Playful, youthful female")
        ]

    def extract_scenes_and_turns(self, raw_text: str) -> Tuple[List[ScenePlan], List[Dict[str, Any]]]:
        """
        Parses text for scenes (e.g. '[Scene: Castle Gate - Night]', 'EXT. FOREST - DAY')
        and dialogue turns ('John:', '[Commander]', etc.).
        """
        scenes: List[ScenePlan] = []
        turns: List[Dict[str, Any]] = []

        current_scene_idx = 1
        current_scene_id = "scene_1"
        current_scene = ScenePlan(
            scene_id=current_scene_id,
            scene_index=current_scene_idx,
            scene_name="Prologue",
            location="General",
            mood="neutral"
        )
        scenes.append(current_scene)

        # Split on newlines
        raw_lines = [l.strip() for l in raw_text.splitlines() if l.strip()]

        for line in raw_lines:
            # Check for scene header: [Scene: ...], INT. ..., EXT. ..., Scene N:
            scene_match = re.match(r'^(?:\[Scene\s*:\s*([^\]]+)\]|(?:INT\.|EXT\.)\s+([^\n-]+)(?:-\s*([^\n]+))?|Scene\s+(\d+)\s*:\s*(.+))$', line, re.IGNORECASE)
            if scene_match:
                current_scene_idx += 1
                current_scene_id = f"scene_{current_scene_idx}"
                name = (scene_match.group(1) or scene_match.group(2) or scene_match.group(5) or f"Scene {current_scene_idx}").strip()
                tod = (scene_match.group(3) or "").strip()
                mood = "suspense" if any(w in name.lower() for w in ["night", "dark", "dungeon", "storm"]) else "neutral"
                
                new_scene = ScenePlan(
                    scene_id=current_scene_id,
                    scene_index=current_scene_idx,
                    scene_name=name,
                    location=name,
                    time_of_day=tod or "Day",
                    mood=mood,
                    dramatic_intensity=0.7 if mood == "suspense" else 0.5
                )
                scenes.append(new_scene)
                current_scene = new_scene
                continue

            # Check if line contains inline speaker changes
            sub_turns = re.split(r'(?<=[.!?…])\s+(?=(?:\[[A-Za-z0-9_\s]+\]|[A-Za-z0-9_\s]{2,20})\s*:)', line)
            for st in sub_turns:
                st = st.strip()
                if not st:
                    continue

                spk, clean_text = self._extract_speaker(st)
                turns.append({
                    "speaker": spk,
                    "text": clean_text,
                    "scene_id": current_scene_id,
                    "raw_line": st
                })
                if spk and spk not in current_scene.characters:
                    current_scene.characters.append(spk)

        return scenes, turns

    def _extract_speaker(self, line: str) -> Tuple[Optional[str], str]:
        """
        Supports:
        - Speaker: Text
        - [Speaker]: Text
        - [Speaker] Text
        """
        line_clean = line.strip()
        
        # 1. Matches '[Speaker]: Text' or '[Speaker] Text'
        match_bracket = re.match(r'^\[([A-Za-z0-9_\s]{2,25})\]\s*:?\s*(.+)$', line_clean)
        if match_bracket:
            spk = match_bracket.group(1).strip()
            text = match_bracket.group(2).strip()
            text = re.sub(r'^["\']|["\']$', '', text)
            return (spk, text)

        # 2. Matches 'Speaker: Text'
        match_colon = re.match(r'^([A-Za-z0-9_\s]{2,25})\s*:\s*(.+)$', line_clean)
        if match_colon:
            spk = match_colon.group(1).strip()
            text = match_colon.group(2).strip()
            text = re.sub(r'^["\']|["\']$', '', text)
            return (spk, text)

        return (None, line_clean)

    def auto_cast_characters(
        self,
        speakers: List[str],
        language: str = "en",
        style_preference: str = "Cinematic",
        existing_characters: Optional[List[ProjectCharacter]] = None,
        locked_characters: Optional[List[str]] = None,
        character_overrides: Optional[Dict[str, str]] = None,
        default_voice_id: str = "en-US-ChristopherNeural"
    ) -> Dict[str, ProjectCharacter]:
        """
        Auto Cast 2.0:
        Guarantees character-to-voice consistency across the entire project.
        Considers role, gender, style, language, and locks.
        """
        existing_map: Dict[str, ProjectCharacter] = {}
        if existing_characters:
            for ec in existing_characters:
                existing_map[ec.character_id.lower()] = ec
                existing_map[ec.speaker_name.lower()] = ec

        locked_set = set(k.lower() for k in (locked_characters or []))
        overrides_map = {k.lower(): v for k, v in (character_overrides or {}).items()}

        cast: Dict[str, ProjectCharacter] = {}
        assigned_voice_ids: set = set()

        male_idx = 0
        female_idx = 0

        # Known female names
        female_names = {"sarah", "mary", "elena", "maria", "emma", "jenny", "aria", "anna", "lisa", "sophia", "rachel", "claire"}
        male_names = {"john", "david", "michael", "sam", "peter", "alex", "thomas", "james", "william", "robert", "brian"}

        for spk in speakers:
            spk_key = spk.lower()

            # STEP 7: Check if already locked or previously mapped in this project
            if spk_key in existing_map:
                prev_char = existing_map[spk_key]
                # If user provided explicit override, use it
                if spk_key in overrides_map:
                    new_vid = overrides_map[spk_key]
                    cast[spk_key] = ProjectCharacter(
                        character_id=spk_key,
                        speaker_name=spk,
                        voice_id=new_vid,
                        provider="edge-tts",
                        is_locked=True,
                        style=prev_char.style,
                        confidence=1.0,
                        reason="Explicit user voice override"
                    )
                else:
                    cast[spk_key] = prev_char
                assigned_voice_ids.add(cast[spk_key].voice_id)
                continue

            # Check explicit override
            if spk_key in overrides_map:
                vid = overrides_map[spk_key]
                cast[spk_key] = ProjectCharacter(
                    character_id=spk_key,
                    speaker_name=spk,
                    voice_id=vid,
                    provider="edge-tts",
                    is_locked=True,
                    style=style_preference,
                    confidence=1.0,
                    reason="Explicit user voice override"
                )
                assigned_voice_ids.add(vid)
                continue

            # Language specific casting (Urdu/Hindi)
            if "ur" in language.lower() or "roman" in language.lower():
                is_f = any(k in spk_key for k in ["female", "aurat", "larki", "mother", "maa", "begum", "sister", "woman"]) or spk_key in female_names
                vid = "ur-PK-UzmaNeural" if is_f else "ur-PK-AsadNeural"
                cast[spk_key] = ProjectCharacter(
                    character_id=spk_key,
                    speaker_name=spk,
                    voice_id=vid,
                    provider="edge-tts",
                    is_locked=spk_key in locked_set,
                    style=style_preference,
                    confidence=0.98,
                    reason=f"Native Urdu voice profile for {spk}"
                )
                assigned_voice_ids.add(vid)
                continue

            if "hi" in language.lower():
                is_f = any(k in spk_key for k in ["female", "aurat", "larki", "mother", "sister", "woman"]) or spk_key in female_names
                vid = "hi-IN-SwaraNeural" if is_f else "hi-IN-MadhurNeural"
                cast[spk_key] = ProjectCharacter(
                    character_id=spk_key,
                    speaker_name=spk,
                    voice_id=vid,
                    provider="edge-tts",
                    is_locked=spk_key in locked_set,
                    style=style_preference,
                    confidence=0.98,
                    reason=f"Native Hindi voice profile for {spk}"
                )
                assigned_voice_ids.add(vid)
                continue

            # Check Archetype Map
            matched_arch = None
            for arch_key, arch_data in self.archetypes.items():
                if arch_key in spk_key:
                    matched_arch = arch_data
                    break

            if matched_arch:
                cast[spk_key] = ProjectCharacter(
                    character_id=spk_key,
                    speaker_name=spk,
                    voice_id=matched_arch["voice_id"],
                    provider="edge-tts",
                    is_locked=spk_key in locked_set,
                    style=matched_arch["style"],
                    confidence=0.96,
                    reason=matched_arch["reason"]
                )
                assigned_voice_ids.add(matched_arch["voice_id"])
                continue

            # Gender/Name heuristic fallback with voice diversity
            if spk_key in female_names or any(w in spk_key for w in ["girl", "woman", "lady", "sister", "mother", "female", "miss", "mrs"]):
                # Pick female voice that isn't assigned yet if possible
                chosen_v = self.female_voice_pool[female_idx % len(self.female_voice_pool)]
                female_idx += 1
                cast[spk_key] = ProjectCharacter(
                    character_id=spk_key,
                    speaker_name=spk,
                    voice_id=chosen_v[0],
                    provider="edge-tts",
                    is_locked=spk_key in locked_set,
                    style=chosen_v[1],
                    confidence=0.92,
                    reason=f"Female dialogue match: {chosen_v[2]}"
                )
                assigned_voice_ids.add(chosen_v[0])
            else:
                # Pick male/general voice
                chosen_v = self.male_voice_pool[male_idx % len(self.male_voice_pool)]
                male_idx += 1
                cast[spk_key] = ProjectCharacter(
                    character_id=spk_key,
                    speaker_name=spk,
                    voice_id=chosen_v[0],
                    provider="edge-tts",
                    is_locked=spk_key in locked_set,
                    style=chosen_v[1],
                    confidence=0.92,
                    reason=f"Character archetype match: {chosen_v[2]}"
                )
                assigned_voice_ids.add(chosen_v[0])

        return cast

    def plan_speech(
        self,
        normalized_text: str,
        emotion_mode: str = "auto",
        custom_pronunciations: Optional[Dict[str, str]] = None,
        base_voice_id: str = "en-US-ChristopherNeural",
        language: str = "en",
        style_preference: str = "Cinematic",
        characters_map: Optional[Dict[str, ProjectCharacter]] = None
    ) -> Tuple[List[ScenePlan], List[ChunkPlan]]:
        """
        Main execution method for Module 8.
        Parses scenes and dialogue turns, applies pronunciation substitutions,
        resolves character voices from the casting map, and calculates prosody.
        """
        scenes, turns = self.extract_scenes_and_turns(normalized_text)

        chunks: List[ChunkPlan] = []
        chunk_idx = 1

        for turn in turns:
            spk = turn.get("speaker")
            clean_text = turn["text"]
            scene_id = turn.get("scene_id")

            # Resolve assigned voice from cast map
            assigned_voice = base_voice_id
            char_id = None
            if spk and characters_map:
                spk_lower = spk.lower()
                if spk_lower in characters_map:
                    assigned_voice = characters_map[spk_lower].voice_id
                    char_id = characters_map[spk_lower].character_id

            # Keep dialogue turns as single natural performance chunks unless very long (>30 words)
            if spk and len(clean_text.split()) <= 30:
                raw_sentences = [clean_text]
            else:
                raw_sentences = re.split(r'(?<=[.!?…])\s+', clean_text)

            for raw_s in raw_sentences:
                s = raw_s.strip()
                if not s:
                    continue

                # Long sentence clause splitting (>25 words)
                sub_clauses = [s]
                if len(s.split()) > 25 and (',' in s or ';' in s or '—' in s):
                    sub_clauses = [c.strip() for c in re.split(r'(?<=[,;—])\s+', s) if c.strip()]

                for clause in sub_clauses:
                    spoken_form = self.pronunciation_agent.apply_pronunciations(clause, custom_pronunciations)
                    performance = self.emotion_agent.analyze_sentence_performance(clause, emotion_mode)

                    plan = ChunkPlan(
                        chunk_index=chunk_idx,
                        text=clause,
                        normalized_text=clause,
                        spoken_text=spoken_form,
                        character_id=char_id or (spk.lower() if spk else None),
                        speaker_name=spk,
                        speaker=spk,
                        voice_id=assigned_voice,
                        assigned_voice_id=assigned_voice,
                        provider="edge-tts",
                        scene_id=scene_id,
                        emotion=performance["emotion"],
                        emotion_intensity=performance["intensity"],
                        dramatic_intensity=performance.get("intensity", 0.5),
                        speed=performance["speed"],
                        pitch=performance["pitch"],
                        rate=performance["rate"],
                        pause_before_ms=performance["pause_before_ms"],
                        pause_after_ms=performance["pause_after_ms"],
                        stress_words=performance["stress_words"]
                    )
                    chunks.append(plan)
                    chunk_idx += 1

        return scenes, chunks
