import re
from typing import Dict, Tuple

class ScriptIntelligenceAgent:
    """
    Module 2: Script Intelligence Agent
    Handles Language Identification, Code-Switching Detection,
    and Conversational/Speech-friendly Text Normalization (Numbers, Dates, Acronyms).
    """

    def __init__(self):
        # Common historical and military acronyms
        self.abbreviations: Dict[str, str] = {
            "WWII": "World War Two",
            "WW2": "World War Two",
            "WWI": "World War One",
            "WW1": "World War One",
            "B-25": "B twenty-five",
            "B-29": "B twenty-nine",
            "B-52": "B fifty-two",
            "AK-47": "A K forty-seven",
            "M16": "M sixteen",
            "U.S.": "U S",
            "USA": "U S A",
            "UK": "U K",
            "NASA": "NASA",
            "FBI": "F B I",
            "CIA": "C I A",
            "AI": "A I",
            "TTS": "T T S",
            "QC": "Q C",
            "ASR": "A S R",
            "Dr.": "Doctor",
            "Mr.": "Mister",
            "Mrs.": "Missus",
            "Ms.": "Miss",
            "vs.": "versus",
            "etc.": "et cetera",
            "e.g.": "for example",
            "i.e.": "that is"
        }

    def detect_language(self, text: str) -> Tuple[str, str]:
        """
        Detects primary language and whether code-switching / Roman Urdu is present.
        Returns: (language_code, description)
        """
        # Check for Arabic/Persian/Urdu script unicode range \u0600-\u06FF
        has_arabic_script = bool(re.search(r'[\u0600-\u06FF]', text))
        if has_arabic_script:
            return ("ur", "Urdu (Nastaliq script)")
            
        # Check for Devanagari script unicode range \u0900-\u097F
        has_devanagari = bool(re.search(r'[\u0900-\u097F]', text))
        if has_devanagari:
            return ("hi", "Hindi (Devanagari script)")

        # Roman Urdu / Hinglish keyword heuristics (avoiding pure English words like 'the')
        roman_indic_markers = [
            r"\b(usne|unhone|kaha|gaya|gayi|mera|meri|humne|tumhe|aapne|karna|hoga|raha|rahi|lekin|magar|aur|kyun|kyunki|darwaza|khola|aawaz|raat|khamoshi|nahi|bhi|bohat|makan|purane|shayed|insani|taqat)\b"
        ]
        text_lower = text.lower()
        matches = sum(len(re.findall(pattern, text_lower)) for pattern in roman_indic_markers)
        
        words = text.split()
        if len(words) > 0 and matches >= 2 and (matches / max(len(words), 1)) > 0.08:
            return ("roman_urdu", "Roman Urdu / Hinglish Code-Switching")

        return ("en", "English")

    def normalize_numbers_and_dates(self, text: str) -> str:
        """Converts years, currency, percentages, and standard numbers into speech form."""
        # 4-digit years like 1944, 2024, 1812
        def replace_year(match):
            val = int(match.group(0))
            if 1800 <= val <= 1999:
                century = val // 100
                remainder = val % 100
                if remainder == 0:
                    return f"{self._two_digit_to_words(century)} hundred"
                return f"{self._two_digit_to_words(century)} {self._two_digit_to_words(remainder)}"
            elif 2000 <= val <= 2009:
                return f"two thousand {self._two_digit_to_words(val % 100)}" if val % 100 > 0 else "two thousand"
            elif 2010 <= val <= 2099:
                return f"twenty {self._two_digit_to_words(val % 100)}"
            return str(val)

        # Match standalone 4 digit years
        text = re.sub(r'\b(1[89]\d{2}|20\d{2})\b', replace_year, text)

        # Percentages
        text = re.sub(r'(\d+)%', r'\1 percent', text)

        # Currency
        text = re.sub(r'\$(\d+)', r'\1 dollars', text)
        text = re.sub(r'£(\d+)', r'\1 pounds', text)

        # Common simple single and double digit numbers
        num_map = {
            "0": "zero", "1": "one", "2": "two", "3": "three", "4": "four",
            "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine",
            "10": "ten", "11": "eleven", "12": "twelve", "13": "thirteen",
            "14": "fourteen", "15": "fifteen", "16": "sixteen", "17": "seventeen",
            "18": "eighteen", "19": "nineteen", "20": "twenty", "30": "thirty",
            "40": "forty", "50": "fifty", "60": "sixty", "70": "seventy",
            "80": "eighty", "90": "ninety", "100": "one hundred"
        }
        for digit, word in num_map.items():
            text = re.sub(rf'\b{digit}\b', word, text)

        return text

    def _two_digit_to_words(self, n: int) -> str:
        ones = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
                "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
                "seventeen", "eighteen", "nineteen"]
        tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
        if n < 20:
            return ones[n]
        rem = n % 10
        if rem == 0:
            return tens[n // 10]
        return f"{tens[n // 10]}-{ones[rem]}"

    def apply_abbreviations(self, text: str) -> str:
        for abbr, spoken in self.abbreviations.items():
            pattern = rf'(?<!\w){re.escape(abbr)}(?!\w)'
            text = re.sub(pattern, spoken, text)
        return text

    def normalize(self, text: str) -> Tuple[str, str, str]:
        """
        Main execution pipeline for Module 2.
        Returns: (normalized_text, language_code, language_description)
        """
        lang_code, lang_desc = self.detect_language(text)
        
        # Strip excessive markdown formatting while preserving line breaks for multi-speaker dialogues
        cleaned = re.sub(r'[*_#`~]', '', text)
        lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in cleaned.splitlines()]
        cleaned = '\n'.join([line for line in lines if line])

        # Apply abbreviations
        cleaned = self.apply_abbreviations(cleaned)

        # Apply numbers and dates normalization for spoken naturalness
        normalized = self.normalize_numbers_and_dates(cleaned)

        return (normalized, lang_code, lang_desc)
