import re
from typing import List, Dict, Optional, Tuple, Any
from ..models.schemas import ChunkPlan, ProjectCharacter, ScenePlan
from .emotion_performance import EmotionPerformanceAgent
from .pronunciation import PronunciationAgent
from .script_intelligence import ScriptIntelligenceAgent
from ..core.voice_catalog import VOICE_CATALOG, find_voice_by_id_or_profile

class SpeechPlannerAgent:
    """
    Module 8 & Auto Cast 2.0:
    Intelligent Script, Scene, and Multi-Character Speech Planner.
    Supports dialogue-style scripts ('John:', '[Commander]', etc.),
    scene detection, character voice casting with consistency guarantees,
    and performance direction.
    """

    def __init__(
        self,
        emotion_agent: EmotionPerformanceAgent,
        pronunciation_agent: PronunciationAgent,
        script_agent: Optional[ScriptIntelligenceAgent] = None
    ):
        self.emotion_agent = emotion_agent
        self.pronunciation_agent = pronunciation_agent
        self.script_agent = script_agent or ScriptIntelligenceAgent()

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

    def parse_speaker_info(self, raw_spk: str) -> Dict[str, str]:
        """
        Parses raw speaker string into clean display name, identifier, and detected gender.
        Examples:
        - 'Voice 1 (Ibrar)' -> {'name': 'Ibrar', 'id': 'ibrar', 'gender': 'male'}
        - 'Voice 2 (Ayesha)' -> {'name': 'Ayesha', 'id': 'ayesha', 'gender': 'female'}
        - 'Voice 1' -> {'name': 'Voice 1', 'id': 'voice_1', 'gender': 'male'}
        - 'Voice 2' -> {'name': 'Voice 2', 'id': 'voice_2', 'gender': 'female'}
        - 'Ayesha' -> {'name': 'Ayesha', 'id': 'ayesha', 'gender': 'female'}
        - 'Ibrar' -> {'name': 'Ibrar', 'id': 'ibrar', 'gender': 'male'}
        """
        if not raw_spk:
            return {"name": "Narrator", "id": "narrator", "gender": "male", "raw": ""}

        raw = raw_spk.strip()
        m_paren = re.search(r'[\(\[\{]([^\)\]\}]+)[\)\]\}]', raw)
        m_dash = re.search(r'[-—]\s*([A-Za-z0-9_\u0600-\u06FF\s]+)', raw)
        
        display_name = raw
        if m_paren:
            cand = m_paren.group(1).strip()
            if cand.lower() not in ["male", "female", "mard", "aurat", "man", "woman"]:
                display_name = cand
        elif m_dash:
            cand = m_dash.group(1).strip()
            if cand.lower() not in ["male", "female", "mard", "aurat", "man", "woman"]:
                display_name = cand

        # Clean display name from generic Voice / Speaker prefixes
        display_name = re.sub(r'^(?:Voice|Speaker|Character|Turn|V)\s*\d+[\s:\-_]*', '', display_name, flags=re.IGNORECASE).strip()
        if not display_name:
            display_name = raw

        gender = self.detect_speaker_gender(display_name, raw)
        spk_id = re.sub(r'[^a-z0-9_]+', '_', display_name.lower()).strip('_') or "speaker"

        return {
            "name": display_name,
            "id": spk_id,
            "gender": gender,
            "raw": raw
        }

    def detect_speaker_gender(self, name: str, raw_tag: str = "") -> str:
        """
        Infers whether a character should speak in a Female or Male voice.
        Follows user specification:
        - Voice 1 / Ibrar / Male tags -> Male Voice
        - Voice 2 / Ayesha / Female tags -> Female Voice
        """
        combined = f"{name} {raw_tag}".lower()

        # 1. Explicit female keywords
        if any(w in combined for w in [
            "female", "woman", "lady", "girl", "aurat", "larki", "khatoon", "begum",
            "mother", "maa", "sister", "bhen", "adi", "marvi", "queen", "princess",
            "witch", "daughter", "miss", "mrs", "femme", "عورت", "لڑکی", "ماں", "بہن"
        ]):
            return "female"

        # 2. Explicit male keywords
        if any(w in combined for w in [
            "male", "man", "boy", "gentleman", "mard", "larka", "bhai", "brother",
            "father", "baap", "king", "prince", "commander", "captain", "soldier",
            "doctor", "scientist", "villain", "son", "mr", "مرد", "لڑکا", "بھائی"
        ]):
            return "male"

        # 3. Voice 2 / Voice 4 / Even numbered voices -> Female
        if re.search(r'\b(?:voice|speaker|v|آواز)\s*(?:2|4|6|two|four|six|۲|۴)\b', combined):
            return "female"

        # 4. Voice 1 / Voice 3 / Odd numbered voices -> Male
        if re.search(r'\b(?:voice|speaker|v|آواز)\s*(?:1|3|5|one|three|five|۱|۳)\b', combined):
            return "male"

        # 5. Known female names database
        female_names = {
            "ayesha", "aisha", "fatima", "zainab", "sana", "amna", "maria", "hira",
            "maryam", "rabia", "sadia", "uzma", "marvi", "zara", "noor", "kinza",
            "mehwish", "bushra", "iqra", "sidra", "kiran", "farah", "asma", "saima",
            "nida", "samina", "tania", "alina", "anaya", "sarah", "mary", "elena",
            "emma", "jenny", "aria", "anna", "lisa", "sophia", "rachel", "claire",
            "ava", "sonia", "priya", "pooja", "neha", "ananya", "deepika", "katrina",
            "sassui", "suhni", "sorath", "momal", "adi", "bakhtawar", "benazir",
            "عائشہ", "فاطمہ", "زینب", "ثنا", "مریم", "عظمیٰ", "مارئی", "سسئی", "سوہݨی"
        }
        for token in re.findall(r'[a-zA-Z\u0600-\u06FF]+', combined):
            if token in female_names:
                return "female"

        # 6. Known male names database
        male_names = {
            "ibrar", "ali", "ahmed", "usman", "bilal", "hamza", "asad", "tariq",
            "omar", "omer", "daniyal", "hassan", "hussain", "fahad", "waqas",
            "sarang", "babar", "imran", "kamran", "rizwan", "salman", "arslan",
            "adnan", "noman", "farhan", "rashid", "kashif", "shahid", "khalid",
            "saad", "john", "david", "michael", "sam", "peter", "alex", "thomas",
            "james", "william", "robert", "brian", "roger", "guy", "eric", "andrew",
            "rahul", "rohit", "amit", "raj", "saeen", "sain", "ada", "bachal",
            "soomro", "shah", "latif", "jamali", "bhittai", "punhoon", "channa",
            "ابرار", "علی", "احمد", "اسد", "عثمان", "سارنگ", "لطیف", "سومرو", "سائیں"
        }
        for token in re.findall(r'[a-zA-Z\u0600-\u06FF]+', combined):
            if token in male_names:
                return "male"

        return "male"

    def extract_scenes_and_turns(self, raw_text: str) -> Tuple[List[ScenePlan], List[Dict[str, Any]]]:
        """
        Parses text for scenes and dialogue turns with stateful multi-line tracking
        and inline turn splitting. Completely strips speaker tags from the dialogue text.
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

        # Stateful current speaker tracking across lines
        current_speaker: Optional[str] = None

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

            # Check if line contains inline speaker changes (e.g. "Voice 1: Hello. Voice 2: Hi.")
            inline_pattern = r'(?<=[.!?…])\s+(?=(?:\[[^\]]+\]|\([^\)]+\)|(?:Voice|Speaker|Character|Actor|Turn|V|آواز)\s*\d+|[A-Za-z0-9_\u0600-\u06FF]{2,20})\s*[:\-])'
            sub_turns = re.split(inline_pattern, line, flags=re.IGNORECASE)

            for st in sub_turns:
                st = st.strip()
                if not st:
                    continue

                spk, clean_text = self._extract_speaker(st)
                if spk:
                    current_speaker = spk

                effective_spk = spk or current_speaker
                
                # If the line was only a speaker header like 'Voice 1 (Ibrar):', clean_text is empty
                if not clean_text:
                    continue

                # Clean any lingering speaker labels from the start of dialogue text
                clean_text = re.sub(r'^(?:\[[^\]]+\]|\([^\)]+\)|(?:Voice|Speaker|Character|V|آواز)\s*\d+(?:\s*[\(\-][^\)]*[\)])?|[A-Za-z0-9_\u0600-\u06FF]{2,25})\s*[:\-]\s*', '', clean_text, flags=re.IGNORECASE).strip()
                if not clean_text:
                    continue

                info = self.parse_speaker_info(effective_spk) if effective_spk else None
                speaker_display = info["name"] if info else None

                turns.append({
                    "speaker": effective_spk,
                    "speaker_name": speaker_display,
                    "text": clean_text,
                    "scene_id": current_scene_id,
                    "raw_line": st
                })
                if speaker_display and speaker_display not in current_scene.characters:
                    current_scene.characters.append(speaker_display)

        return scenes, turns

    def _extract_speaker(self, line: str) -> Tuple[Optional[str], str]:
        """
        Extracts speaker and strips speaker labels completely from the dialogue text.
        Supports:
        - Voice 1 (Ibrar): Text / Voice 2 (Ayesha): Text
        - [Voice 1 - Male]: Text / [Voice 2 - Female]: Text
        - [Voice 1] Text / [Voice 2] Text
        - Voice 1: Text / Voice 2: Text
        - Ibrar: Text / Ayesha: Text
        - Voice 1 - Text / Voice 2 - Text
        """
        line_clean = line.strip()
        if not line_clean:
            return (None, "")

        # 1. Bracket format: [Voice 1 (Ibrar)]: Text or [Voice 1] Text
        m_bracket = re.match(r'^\[([^\]]+)\]\s*:?\s*(.*)$', line_clean)
        if m_bracket:
            spk = m_bracket.group(1).strip()
            text = m_bracket.group(2).strip()
            text = re.sub(r'^["\']|["\']$', '', text).strip()
            return (spk, text)

        # 2. Parentheses at line start: (Voice 1 (Ibrar)): Text or (Voice 1): Text
        m_paren = re.match(r'^\(([^\)]+)\)\s*:?\s*(.*)$', line_clean)
        if m_paren:
            spk = m_paren.group(1).strip()
            text = m_paren.group(2).strip()
            text = re.sub(r'^["\']|["\']$', '', text).strip()
            return (spk, text)

        # 3. Colon format: Voice 1 (Ibrar): Text, Voice 2: Text, Ibrar: Text, Ayesha: Text
        m_colon = re.match(r'^([A-Za-z0-9_\s\u0600-\u06FF\(\)\-\.]+?)\s*:\s*(.*)$', line_clean)
        if m_colon:
            candidate_spk = m_colon.group(1).strip()
            text = m_colon.group(2).strip()
            non_speakers = {"note", "warning", "ps", "p.s", "step", "tip", "caution", "important", "remember", "time", "date"}
            if len(candidate_spk) <= 35 and candidate_spk.lower() not in non_speakers and not candidate_spk.isdigit():
                text = re.sub(r'^["\']|["\']$', '', text).strip()
                return (candidate_spk, text)

        # 4. Dash format for voice tags: Voice 1 - Text or Voice 1 (Ibrar) - Text
        m_dash = re.match(r'^((?:Voice|Speaker|Character|Turn|V)\s*\d+(?:\s*[\(\-][^\)]*[\)])?)\s*[-—]\s*(.*)$', line_clean, re.IGNORECASE)
        if m_dash:
            spk = m_dash.group(1).strip()
            text = m_dash.group(2).strip()
            text = re.sub(r'^["\']|["\']$', '', text).strip()
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
        Auto Cast 2.0 with Gender & Voice Intelligence:
        Automatically assigns male voices to male speakers (Voice 1, Ibrar, etc.)
        and female voices to female speakers (Voice 2, Ayesha, etc.).
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

        for spk in speakers:
            spk_key = spk.lower()
            info = self.parse_speaker_info(spk)
            display_name = info["name"]
            gender = info["gender"]
            spk_id = info["id"]

            # 1. Check existing locked or mapped character
            if spk_key in existing_map or spk_id in existing_map or display_name.lower() in existing_map:
                prev_char = existing_map.get(spk_key) or existing_map.get(spk_id) or existing_map.get(display_name.lower())
                if spk_key in overrides_map:
                    new_vid = overrides_map[spk_key]
                    p_char = ProjectCharacter(
                        character_id=spk_id,
                        speaker_name=display_name,
                        voice_id=new_vid,
                        provider="edge-tts",
                        is_locked=True,
                        style=prev_char.style if prev_char else style_preference,
                        confidence=1.0,
                        reason="Explicit user voice override"
                    )
                else:
                    p_char = prev_char
                cast[spk_key] = p_char
                cast[display_name.lower()] = p_char
                cast[spk_id] = p_char
                assigned_voice_ids.add(p_char.voice_id)
                continue

            # 2. Check explicit override
            if spk_key in overrides_map or display_name.lower() in overrides_map or spk_id in overrides_map:
                vid = overrides_map.get(spk_key) or overrides_map.get(display_name.lower()) or overrides_map.get(spk_id)
                p_char = ProjectCharacter(
                    character_id=spk_id,
                    speaker_name=display_name,
                    voice_id=vid,
                    provider="edge-tts",
                    is_locked=True,
                    style=style_preference,
                    confidence=1.0,
                    reason="Explicit user voice override"
                )
                cast[spk_key] = p_char
                cast[display_name.lower()] = p_char
                cast[spk_id] = p_char
                assigned_voice_ids.add(vid)
                continue

            # 3. Urdu & Roman Urdu Casting (ur-PK-UzmaNeural for Female, ur-PK-AsadNeural for Male)
            if "ur" in language.lower() or "roman_urdu" in language.lower() or ("roman" in language.lower() and "sindhi" not in language.lower()):
                vid = "ur-PK-UzmaNeural" if gender == "female" else "ur-PK-AsadNeural"
                p_char = ProjectCharacter(
                    character_id=spk_id,
                    speaker_name=display_name,
                    voice_id=vid,
                    provider="edge-tts",
                    is_locked=spk_key in locked_set,
                    style=style_preference,
                    confidence=0.99,
                    reason=f"Native Urdu {'Female' if gender == 'female' else 'Male'} voice for {display_name}"
                )
                cast[spk_key] = p_char
                cast[display_name.lower()] = p_char
                cast[spk_id] = p_char
                assigned_voice_ids.add(vid)
                continue

            # 4. Sindhi & Roman Sindhi Casting
            if any(term in language.lower() for term in ["sd", "sindhi"]):
                vid = "ur-PK-UzmaNeural" if gender == "female" else "ur-PK-AsadNeural"
                p_char = ProjectCharacter(
                    character_id=spk_id,
                    speaker_name=display_name,
                    voice_id=vid,
                    provider="edge-tts",
                    is_locked=spk_key in locked_set,
                    style=style_preference,
                    confidence=0.99,
                    reason=f"Authentic Sindhi {'Female' if gender == 'female' else 'Male'} voice for {display_name}"
                )
                cast[spk_key] = p_char
                cast[display_name.lower()] = p_char
                cast[spk_id] = p_char
                assigned_voice_ids.add(vid)
                continue

            # 5. Hindi Casting
            if "hi" in language.lower():
                vid = "hi-IN-SwaraNeural" if gender == "female" else "hi-IN-MadhurNeural"
                p_char = ProjectCharacter(
                    character_id=spk_id,
                    speaker_name=display_name,
                    voice_id=vid,
                    provider="edge-tts",
                    is_locked=spk_key in locked_set,
                    style=style_preference,
                    confidence=0.98,
                    reason=f"Native Hindi {'Female' if gender == 'female' else 'Male'} voice for {display_name}"
                )
                cast[spk_key] = p_char
                cast[display_name.lower()] = p_char
                cast[spk_id] = p_char
                assigned_voice_ids.add(vid)
                continue

            # 6. English & Global Voice Pool Casting
            if gender == "female":
                chosen_v = self.female_voice_pool[female_idx % len(self.female_voice_pool)]
                female_idx += 1
                p_char = ProjectCharacter(
                    character_id=spk_id,
                    speaker_name=display_name,
                    voice_id=chosen_v[0],
                    provider="edge-tts",
                    is_locked=spk_key in locked_set,
                    style=chosen_v[1],
                    confidence=0.95,
                    reason=f"Female dialogue voice ({chosen_v[2]}) for {display_name}"
                )
            else:
                chosen_v = self.male_voice_pool[male_idx % len(self.male_voice_pool)]
                male_idx += 1
                p_char = ProjectCharacter(
                    character_id=spk_id,
                    speaker_name=display_name,
                    voice_id=chosen_v[0],
                    provider="edge-tts",
                    is_locked=spk_key in locked_set,
                    style=chosen_v[1],
                    confidence=0.95,
                    reason=f"Male dialogue voice ({chosen_v[2]}) for {display_name}"
                )

            cast[spk_key] = p_char
            cast[display_name.lower()] = p_char
            cast[spk_id] = p_char
            assigned_voice_ids.add(p_char.voice_id)

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
            speaker_display = spk
            if spk:
                info = self.parse_speaker_info(spk)
                speaker_display = info["name"]
                if characters_map:
                    for candidate_key in [spk.lower(), info["name"].lower(), info["id"]]:
                        if candidate_key in characters_map:
                            assigned_voice = characters_map[candidate_key].voice_id
                            char_id = characters_map[candidate_key].character_id
                            break

            # Strip any lingering speaker labels from the start of clean_text
            clean_text = re.sub(r'^(?:\[[^\]]+\]|\([^\)]+\)|(?:Voice|Speaker|Character|Turn|V|آواز)\s*\d+(?:\s*[\(\-][^\)]*[\)])?|[A-Za-z0-9_\u0600-\u06FF]{2,25})\s*[:\-]\s*', '', clean_text, flags=re.IGNORECASE).strip()
            if not clean_text:
                continue

            # Keep dialogue turns as single natural performance chunks unless very long (>30 words)
            if spk and len(clean_text.split()) <= 30:
                raw_sentences = [clean_text]
            else:
                raw_sentences = re.split(r'(?<=[.!?…])\s+', clean_text)

            for raw_s in raw_sentences:
                s = raw_s.strip()
                if not s:
                    continue

                # Keep sentences unified for natural cadence and prosody unless excessively long (>40 words)
                sub_clauses = [s]
                if len(s.split()) > 40 and (';' in s or '—' in s):
                    parts = [c.strip() for c in re.split(r'(?<=[;—])\s+', s) if c.strip()]
                    if len(parts) > 1:
                        sub_clauses = parts

                for clause in sub_clauses:
                    spoken_form = self.pronunciation_agent.apply_pronunciations(clause, custom_pronunciations)
                    if language in ["roman_urdu", "ur", "roman_sindhi", "sd"]:
                        spoken_form = self.script_agent.transliterate_to_spoken_script(spoken_form, language)
                    performance = self.emotion_agent.analyze_sentence_performance(clause, emotion_mode)

                    # Ensure assigned voice can articulate the language properly
                    actual_voice = assigned_voice
                    if actual_voice.startswith("en-") and language in ["roman_urdu", "ur", "roman_sindhi", "sd"]:
                        gender = self.detect_speaker_gender(speaker_display or spk or "", char_id or "")
                        actual_voice = "ur-PK-UzmaNeural" if gender == "female" else "ur-PK-AsadNeural"

                    gender = self.detect_speaker_gender(speaker_display or spk or "", char_id or "")

                    actual_rate = performance["rate"]
                    if language in ["roman_sindhi", "sd"]:
                        actual_rate = "-6%"  # Slower, resonant, vowel-rich Sindhi cadence
                    elif language in ["roman_urdu", "ur"]:
                        actual_rate = "-3%"

                    actual_pitch = performance["pitch"]
                    if language in ["roman_sindhi", "sd"]:
                        # Deep warm baritone for male Sarang (-2Hz), melodic lyrical warmth for female Marvi (+1Hz)
                        actual_pitch = "+1Hz" if gender == "female" else "-2Hz"

                    if language in ["roman_sindhi", "sd"]:
                        actual_pause_after = max(performance["pause_after_ms"], 420)
                    elif language in ["roman_urdu", "ur"]:
                        actual_pause_after = max(performance["pause_after_ms"], 350)
                    else:
                        actual_pause_after = performance["pause_after_ms"]

                    plan = ChunkPlan(
                        chunk_index=chunk_idx,
                        text=clause,
                        normalized_text=clause,
                        spoken_text=spoken_form,
                        character_id=char_id or (info["id"] if spk else None),
                        speaker_name=speaker_display or spk,
                        speaker=speaker_display or spk,
                        voice_id=actual_voice,
                        assigned_voice_id=actual_voice,
                        provider="edge-tts",
                        scene_id=scene_id,
                        emotion=performance["emotion"],
                        emotion_intensity=performance["intensity"],
                        dramatic_intensity=performance.get("intensity", 0.5),
                        speed=performance["speed"],
                        pitch=actual_pitch,
                        rate=actual_rate,
                        pause_before_ms=performance["pause_before_ms"],
                        pause_after_ms=actual_pause_after,
                        stress_words=performance["stress_words"]
                    )
                    chunks.append(plan)
                    chunk_idx += 1

        return scenes, chunks
