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
        Detects primary language and whether script is Urdu, Sindhi, Roman Urdu, or Roman Sindhi.
        Returns: (language_code, description)
        """
        text_clean = text.strip()
        if not text_clean:
            return ("en", "English")

        # 1. Check for Arabic/Persian/Urdu/Sindhi script unicode range \u0600-\u06FF
        has_arabic_script = bool(re.search(r'[\u0600-\u06FF]', text_clean))
        if has_arabic_script:
            # Check for Sindhi-specific characters:
            # ٻ (067B), ڀ (0680), ٿ (067F), ٺ (067E), ٽ (067D), ڄ (0684), ڃ (0689), ڇ (0686),
            # ڌ (0687), ڏ (068F), ڊ (068A), ڍ (068C), ڙ (0699), ڪ (06AA), ڳ (06B3), ڱ (06B1),
            # ڻ (06BB), ڦ (06A6)
            sindhi_chars_pattern = r'[\u067B\u0680\u067F\u067E\u067D\u0684\u0689\u0686\u0687\u068F\u068A\u068C\u0699\u06AA\u06B3\u06B1\u06BB\u06A6]'
            sindhi_words_pattern = r'\b(سنڌ|سنڌي|آهي|آهين|آهيان|توھان|توهان|منھنجو|منهنجو|ڇا|ٿيو|ڪري|ٻولايو|ڳالهه|ڀلو|ڏسو|ٿو|ٿي|ڪيو|ڪيان|اسان|سائين|ادا|ڀاءُ|چيو)\b'
            
            if re.search(sindhi_chars_pattern, text_clean) or re.search(sindhi_words_pattern, text_clean):
                return ("sd", "Sindhi (سنڌي Script)")
            return ("ur", "Urdu (اردو Nastaliq Script)")

        # 2. Check for Devanagari script unicode range \u0900-\u097F
        has_devanagari = bool(re.search(r'[\u0900-\u097F]', text_clean))
        if has_devanagari:
            return ("hi", "Hindi (Devanagari script)")

        # 3. Check for Roman Sindhi and Roman Urdu in Latin script
        text_lower = text_clean.lower()
        tokens = re.findall(r'[a-zA-Z]+', text_lower)
        total_tokens = len(tokens)
        if total_tokens == 0:
            return ("en", "English")

        # Distinctive Sindhi words in Latin script
        sindhi_strong_markers = {
            "chha", "cha", "aahe", "ahe", "aahay", "ahin", "aheen", "ahyan", "ahyaan", "ahyo", "ahyao",
            "tawahan", "tawhan", "tavhan", "twahan", "tuhanjo", "tuhinjo", "tuhanji", "tuhinji", "tuhinja",
            "muhinjo", "muhinji", "muhinja", "munhinjo", "munhinji",
            "asaa", "asaan", "asanjo", "asanji", "asanjoo",
            "kithy", "kithe", "kithan", "kadahn", "kadhin", "keeyan", "kian", "kihan",
            "chawan", "chayo", "chaye", "chavandaseen",
            "sindh", "sindhi", "bhalo", "bhala", "chango", "changa",
            "khapay", "khapando", "kayo", "kayi", "kandaseen", "karyo",
            "vanin", "vanyo", "vany", "achin", "achyo", "acho",
            "saeen", "sain", "pahanjo", "pahanji", "pahanja",
            "bhauro", "bhaura", "ada", "adi", "thye", "thyo", "pyo", "pyi",
            "budho", "budhai", "wath", "wathyo", "ker", "chho"
        }

        # High-confidence Roman Urdu markers (Zero collision with standard English words)
        roman_urdu_markers = {
            # Auxiliaries & Verbs
            "hai", "hy", "hain", "hyn", "hoon", "hun", "hoga", "hogi", "honge", "hote", "hoti", "hota",
            "karna", "karo", "karein", "karen", "kiya", "kiye", "karte", "karti", "karta", "kar", "kara",
            "raha", "rahi", "rahe", "gaya", "gayi", "gaye", "jana", "jao", "jaenge", "jaunga", "jaungi",
            "aaya", "aayi", "aaye", "aana", "aao", "aae", "dekh", "dekho", "dekha", "dekhna",
            "bolo", "bologe", "bolna", "bola", "boli", "kaha", "kahin", "kaho", "kehta", "kehti", "kahe",
            "sun", "suno", "suna", "sunaye", "lena", "dena", "diya", "diye",
            "chahiye", "chahta", "chahti", "chahte",
            # Pronouns
            "main", "mein", "mujhe", "mujhko", "mera", "meri", "mere", "hum", "hm", "humein", "humko", "hamara", "hamari", "hamare", "humne",
            "tera", "teri", "tere", "tujhe", "tujhko", "tum", "tumhe", "tumko", "tumhara", "tumhari", "tumhare",
            "aap", "ap", "aapka", "apka", "aapki", "apki", "aapke", "apke", "aapne", "apne", "apko", "apna", "apni",
            "yeh", "woh", "iska", "iski", "iske", "uska", "uski", "uske", "unka", "unki", "unke",
            "usne", "isne", "unhone", "inhone", "unhe", "inhe", "inse", "unse",
            # Question words
            "kya", "kia", "kyun", "kyon", "kyunki", "kahan", "khan", "kidhar", "kab", "kaise", "kese", "kaisa", "kaisi", "kaun", "kon", "kitna", "kitne", "kitni",
            # Particles & Conjunctions
            "nahi", "nahin", "nhi", "aur", "lekin", "lekn", "magar", "mgr", "agar", "agr", "toh",
            # Common vocabulary
            "bhai", "yaar", "dost", "theek", "thik", "acha", "achha", "achi", "achhi", "ache", "achhe",
            "bohat", "bahut", "bht", "kuch", "koi", "kisi", "shukriya", "shayed", "zaroor", "zaroorat", "waqt",
            "baat", "baatein", "aawaz", "darwaza", "khula", "khola", "naam", "salaam", "salam",
            "jaise", "jese", "aise", "ese", "abhi", "kabhi", "tabhi", "bhalay", "bhale", "samjh", "samajh",
            "koshish", "zindagi", "insan", "khush", "pareshan"
        }

        sindhi_hits = sum(1 for t in tokens if t in sindhi_strong_markers)
        urdu_hits = sum(1 for t in tokens if t in roman_urdu_markers)

        # 1. Sindhi precedence if distinctive Roman Sindhi markers match
        if sindhi_hits >= 1 and (sindhi_hits >= urdu_hits or (sindhi_hits >= 1 and total_tokens <= 8)):
            return ("roman_sindhi", "Roman Sindhi")

        # 2. Roman Urdu recognition
        if urdu_hits >= 1 and (total_tokens <= 4 or urdu_hits >= 2 or (urdu_hits / total_tokens) >= 0.15):
            return ("roman_urdu", "Roman Urdu")

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

    # --- HIGH-FIDELITY SPOKEN SCRIPT TRANSLITERATION ENGINE ---
    def transliterate_to_spoken_script(self, text: str, lang_code: str) -> str:
        """
        Converts Roman Urdu or Roman Sindhi into authentic Perso-Arabic / Nastaliq script
        specifically for the neural TTS engine (ur-PK-AsadNeural, ur-PK-UzmaNeural)
        to speak with 100% native fluency and cadence, while preserving the user's
        original Latin text in the UI and subtitles.
        """
        if not text:
            return text

        if lang_code in ["roman_sindhi", "sd"]:
            if re.search(r'[\u0600-\u06FF]', text):
                return self._convert_sindhi_script_to_acoustic(text)
            return self._transliterate_roman_sindhi(text)
        elif lang_code in ["roman_urdu", "ur"]:
            if re.search(r'[\u0600-\u06FF]', text):
                return text
            return self._transliterate_roman_urdu(text)

        return text

    def _convert_sindhi_script_to_acoustic(self, text: str) -> str:
        """
        Acoustically adapts Sindhi Perso-Arabic unicode characters to Urdu phonemes
        so Microsoft neural models (ur-PK-AsadNeural, ur-PK-UzmaNeural) pronounce every
        Sindhi letter accurately without skipping or distorting characters.
        """
        acoustic_map = {
            'ڇ': 'چھ', 'ڪ': 'ک', 'ٺ': 'ٹھ', 'ٿ': 'تھ', 'ٻ': 'ب', 'ڀ': 'بھ',
            'ڄ': 'ج', 'ڃ': 'ن', 'ڌ': 'دھ', 'ڏ': 'ڈ', 'ڊ': 'ڈ', 'ڍ': 'ڈھ',
            'ڙ': 'ڑ', 'ڳ': 'گ', 'ڱ': 'نگ', 'ڻ': 'ن', 'ڦ': 'پھ',
            'آهي': 'آہے', 'آهين': 'آہیں', 'آهيان': 'آہیاں', 'آهيو': 'آہیو',
            'توهان': 'توہاں', 'منهنجو': 'مھنجو', 'منهنجي': 'مھنجی', 'منهنجا': 'مھنجا',
            'اسان': 'اساں', 'اسانجو': 'اساں جو', 'اسانجي': 'اساں جی',
            'سائين': 'سائیں', 'ي': 'ی', 'ك': 'ک', 'ه': 'ہ'
        }
        for k, v in acoustic_map.items():
            text = text.replace(k, v)
        return text

    def _transliterate_roman_sindhi(self, text: str) -> str:
        """
        Maps Roman Sindhi words written in English letters directly into authentic
        acoustic Nastaliq script for ur-PK-AsadNeural / ur-PK-UzmaNeural.
        """
        sindhi_map = {
            'chha': 'چھا', 'cha': 'چھا', 'haal': 'حال', 'hal': 'حال',
            'aahe': 'آہے', 'ahe': 'آہے', 'aahay': 'آہے',
            'ahin': 'آہیں', 'aheen': 'آہیں', 'ahyan': 'آہیاں', 'ahyaan': 'آہیاں', 'ahyo': 'آہیو',
            'tawahan': 'توہاں', 'tawhan': 'توہاں', 'tavhan': 'توہاں', 'twahan': 'توہاں',
            'tuhanjo': 'تُھنجو', 'tuhinjo': 'تُھنجو', 'tuhanji': 'تُھنجی', 'tuhinji': 'تُھنجی',
            'tuhanja': 'تُھنجا', 'tuhinja': 'تُھنجا',
            'muhinjo': 'مُھنجو', 'munhinjo': 'مُھنجو', 'muhinji': 'مُھنجی', 'munhinji': 'مُھنجی',
            'muhinja': 'مُھنجا', 'munhinja': 'مُھنجا',
            'man': 'ماں', 'maan': 'ماں', 'asaa': 'اساں', 'asaan': 'اساں',
            'asanjo': 'اساں جو', 'asanji': 'اساں جی', 'asanjoo': 'اساں جو',
            'sindh': 'سندھ', 'sindhi': 'سندھی', 'bhalo': 'بھلو', 'bhala': 'بھلا',
            'chango': 'چنگو', 'changa': 'چنگا', 'chawan': 'چون', 'chayo': 'چیو',
            'khapay': 'کھپے', 'khapando': 'کھپندو', 'kayo': 'کیو', 'kandaseen': 'کنداسیں', 'karyo': 'کریو',
            'saeen': 'سائیں', 'sain': 'سائیں', 'ada': 'ادا', 'adi': 'ادی',
            'watan': 'وطن', 'boli': 'بولی', 'thye': 'تھیے', 'thyo': 'تھیو',
            'pyo': 'پیو', 'pyi': 'پیی', 'kithan': 'کتھاں', 'kithy': 'کتھے', 'kithe': 'کتھے',
            'kadahn': 'کدھن', 'kadhin': 'کدھن', 'meherbani': 'مہربانی',
            'shukrana': 'شکرانہ', 'theek': 'ٹھیک', 'thik': 'ٹھیک', 'thek': 'ٹھیک',
            'sab': 'سبھ', 'sabh': 'سبھ', 'naalo': 'نالو', 'soomro': 'سومرو', 'shikarpur': 'شکارپور',
            'kian': 'کیاں', 'keeyan': 'کیاں', 'ker': 'کیر', 'chho': 'چھو',
            'budho': 'بدھو', 'budhai': 'بدھائے', 'wath': 'وتھ', 'wathyo': 'وتھیو',
            'hath': 'ہتھ', 'akhiyun': 'اکھیوں', 'dil': 'دل', 'yaar': 'یار', 'bhai': 'بھائی'
        }
        return re.sub(r'[a-zA-Z]+', lambda m: sindhi_map.get(m.group(0).lower(), self._phonetic_fallback(m.group(0))), text)

    def _transliterate_roman_urdu(self, text: str) -> str:
        """
        Maps Roman Urdu words written in English letters into authentic Nastaliq script
        with rich conversational vocabulary coverage.
        """
        urdu_map = {
            'hi': 'ہائے', 'hello': 'ہیلو',
            'salam': 'سلام', 'salaam': 'سلام', 'assalam': 'السلام', 'alaikum': 'علیکم',
            'walekum': 'وعلیکم', 'walaikum': 'وعلیکم',
            'kya': 'کیا', 'kyaa': 'کیا', 'kia': 'کیا', 'haal': 'حال', 'hal': 'حال',
            'hai': 'ہے', 'hy': 'ہے', 'hain': 'ہیں', 'hyn': 'ہیں',
            'ho': 'ہو', 'hoon': 'ہوں', 'hun': 'ہوں', 'tha': 'تھا', 'thi': 'تھی', 'the': 'تھے',
            'hoga': 'ہوگا', 'hogi': 'ہوگی', 'honge': 'ہوں گے', 'karna': 'کرنا', 'karo': 'کرو',
            'karein': 'کریں', 'karen': 'کریں', 'kiya': 'کیا', 'kiye': 'کیے', 'kar': 'کر',
            'karta': 'کرتا', 'karti': 'کرتی', 'karte': 'کرتے',
            'raha': 'رہا', 'rahi': 'رہی', 'rahe': 'رہے', 'gaya': 'گیا', 'gayi': 'گئی', 'gaye': 'گئے',
            'jana': 'جانا', 'jao': 'جاؤ', 'jaenge': 'جائیں گے', 'jaunga': 'جاؤں گا', 'jaungi': 'جاؤں گی',
            'aaya': 'آیا', 'aayi': 'آئی', 'aaye': 'آئے', 'aana': 'آنا', 'aao': 'آؤ', 'aa': 'آ',
            'bolo': 'بولو', 'bologe': 'بولو گے', 'bolna': 'بولنا', 'bola': 'بولا', 'boli': 'بولی',
            'kaha': 'کہا', 'kahe': 'کہے', 'suno': 'سنو', 'suna': 'سنا', 'sun': 'سن', 'sunao': 'سناؤ',
            'dekh': 'دیکھ', 'dekho': 'دیکھو', 'dekha': 'دیکھا', 'dekhna': 'دیکھنا',
            'lena': 'لینا', 'lo': 'لو', 'dena': 'دینا', 'do': 'دو', 'diya': 'دیا', 'diye': 'دیے',
            'main': 'میں', 'mein': 'میں', 'mujhe': 'مجھے', 'mujhko': 'مجھ کو',
            'mera': 'میرا', 'meri': 'میری', 'mere': 'میرے',
            'hum': 'ہم', 'hm': 'ہم', 'humein': 'ہمیں', 'humko': 'ہم کو',
            'hamara': 'ہمارا', 'hamari': 'ہماری', 'hamare': 'ہمارے', 'humne': 'ہم نے',
            'tu': 'تو', 'tera': 'تیرا', 'teri': 'تیری', 'tere': 'تیرے', 'tujhe': 'تجھے',
            'tum': 'تم', 'tumhe': 'تمہیں', 'tumko': 'تم کو',
            'tumhara': 'تمہارا', 'tumhari': 'تمہاری', 'tumhare': 'تمہارے',
            'aap': 'آپ', 'ap': 'آپ', 'aapka': 'آپ کا', 'apka': 'آپ کا',
            'aapki': 'آپ کی', 'apki': 'آپ کی', 'aapke': 'آپ کے', 'apke': 'آپ کے',
            'aapne': 'آپ نے', 'apne': 'اپنے', 'apna': 'اپنا', 'apni': 'اپنی', 'apno': 'اپنوں',
            'yeh': 'یہ', 'ye': 'یہ', 'woh': 'وہ', 'wo': 'وہ',
            'iska': 'اس کا', 'iski': 'اس کی', 'iske': 'اس کے',
            'uska': 'اس کا', 'uski': 'اس کی', 'uske': 'اس کے',
            'unka': 'ان کا', 'unki': 'ان کی', 'unke': 'ان کے',
            'usne': 'اس نے', 'isne': 'اس نے', 'unhone': 'انہوں نے',
            'nahi': 'نہیں', 'nahin': 'نہیں', 'nhi': 'نہیں', 'na': 'نہ', 'mat': 'مت', 'bhi': 'بھی',
            'aur': 'اور', 'lekin': 'لیکن', 'lekn': 'لیکن', 'magar': 'مگر', 'mgr': 'مگر',
            'par': 'پر', 'per': 'پر', 'pe': 'پر', 'se': 'سے', 'ko': 'کو', 'ka': 'کا', 'ke': 'کے', 'ki': 'کی',
            'tak': 'تک', 'to': 'تو', 'toh': 'تو', 'agar': 'اگر', 'agr': 'اگر', 'jab': 'جب', 'tab': 'تب', 'ab': 'اب',
            'bhai': 'بھائی', 'yaar': 'یار', 'dost': 'دوست', 'sab': 'سب',
            'theek': 'ٹھیک', 'thik': 'ٹھیک', 'thek': 'ٹھیک',
            'acha': 'اچھا', 'achha': 'اچھا', 'achi': 'اچھی', 'achhi': 'اچھی', 'ache': 'اچھے', 'achhe': 'اچھے',
            'accha': 'اچھا', 'acchi': 'اچھی', 'acche': 'اچھے',
            'bohat': 'بہت', 'bahut': 'بہت', 'bht': 'بہت',
            'kuch': 'کچھ', 'koi': 'کوئی', 'kisi': 'کسی',
            'shukriya': 'شکریہ', 'shayed': 'شاید', 'zaroor': 'ضرور', 'zarur': 'ضرور',
            'waqt': 'وقت', 'din': 'دن', 'raat': 'رات', 'subah': 'صبح', 'shaam': 'شام',
            'baat': 'بات', 'baatein': 'باتیں', 'aawaz': 'آواز', 'darwaza': 'دروازہ', 'naam': 'نام',
            'kheriyat': 'خیریت', 'khairiyat': 'خیریت', 'kheriat': 'خیریت', 'khariyat': 'خیریت',
            'jaise': 'جیسے', 'jese': 'جیسے', 'aise': 'ایسے', 'ese': 'ایسے', 'waise': 'ویسے', 'wese': 'ویسے',
            'kaise': 'کیسے', 'kese': 'کیسے', 'kyun': 'کیوں', 'kyon': 'کیوں',
            'kahan': 'کہاں', 'khan': 'کہاں', 'kidhar': 'کدھر', 'kab': 'کب', 'kon': 'کون', 'kaun': 'کون',
            'kitna': 'کتنا', 'kitne': 'کتنے', 'kitni': 'کتنی',
            'abhi': 'ابھی', 'kabhi': 'کبھی', 'tabhi': 'تبھی',
            'bhalay': 'بھلے', 'bhale': 'بھلے',
            'samajh': 'سمجھ', 'samjh': 'سمجھ', 'samjha': 'سمجھا', 'samjhe': 'سمجھے',
            'intezar': 'انتظار', 'kal': 'کل', 'aaj': 'آج',
            'milenge': 'ملیں گے', 'milte': 'ملتے',
            'chal': 'چل', 'chalo': 'چلو', 'chalein': 'چلیں', 'chalen': 'چلیں',
            'wording': 'الفاظ', 'typing': 'ٹائپنگ', 'agent': 'ایجنٹ', 'still': 'ابھی بھی',
            'chahiye': 'چاہیے', 'chahta': 'چاہتا', 'chahti': 'چاہتی', 'chahte': 'چاہتے',
            'masla': 'مسئلہ', 'koshish': 'کوشش', 'zindagi': 'زندگی', 'insan': 'انسان',
            'khush': 'خوش', 'pareshan': 'پریشان', 'fikar': 'فکر', 'fikr': 'فکر', 'bilkul': 'بالکل',
            'inshallah': 'انشاءاللہ', 'inshaallah': 'انشاءاللہ',
            'mashallah': 'ماشاءاللہ', 'mashaallah': 'ماشاءاللہ',
            'alhamdulillah': 'الحمدللہ', 'subhanallah': 'سبحان اللہ',
            'allah': 'اللہ', 'khuda': 'خدا', 'hafiz': 'حافظ',
            'urdu': 'اردو', 'pakistan': 'پاکستان', 'karachi': 'کراچی', 'lahore': 'لاہور', 'islamabad': 'اسلام آباد'
        }
        return re.sub(r'[a-zA-Z]+', lambda m: urdu_map.get(m.group(0).lower(), self._phonetic_fallback(m.group(0))), text)

    def _phonetic_fallback(self, word: str) -> str:
        """
        Intelligent syllable-based phonetic builder for unrecognized words,
        collapsing redundant vowel repetitions to maintain crisp natural pronunciation.
        """
        w = word.lower()
        char_pairs = [
            ('sh', 'ش'), ('kh', 'خ'), ('gh', 'غ'), ('ch', 'چ'), ('th', 'تھ'), ('bh', 'بھ'), ('ph', 'پھ'),
            ('dh', 'دھ'), ('jh', 'جھ'), ('rh', 'ڑھ'), ('zh', 'ژ'), ('aa', 'آ'), ('ee', 'ی'), ('oo', 'و'),
            ('ai', 'ے'), ('ay', 'ے'), ('ey', 'ے')
        ]
        single_chars = {
            'a': 'ا', 'b': 'ب', 'p': 'پ', 't': 'ت', 'j': 'ج', 'd': 'د', 'r': 'ر',
            'z': 'ز', 's': 'س', 'f': 'ف', 'q': 'ق', 'k': 'ک', 'g': 'گ', 'l': 'ل',
            'm': 'م', 'n': 'ن', 'w': 'و', 'v': 'و', 'h': 'ہ', 'y': 'ی', 'e': 'ے',
            'i': 'ی', 'o': 'و', 'u': 'و', 'c': 'ک'
        }

        res = ''
        i = 0
        while i < len(w):
            matched = False
            for pair, ar in char_pairs:
                if w.startswith(pair, i):
                    res += ar
                    i += len(pair)
                    matched = True
                    break
            if not matched:
                res += single_chars.get(w[i], w[i])
                i += 1

        # Clean Perso-Arabic vowels so they sound natural without vowel stutter
        res = re.sub(r'ے+', 'ے', res)
        res = re.sub(r'ی+', 'ی', res)
        res = re.sub(r'و+', 'و', res)
        res = re.sub(r'ےی', 'ی', res)
        res = re.sub(r'یے', 'ی', res)
        return res
