# Cached version

# hyperparameters: 
#   fuzzy_cutoff : text match cutoff %
import re
from rapidfuzz import process
from functools import lru_cache

DEBUG = True
if DEBUG:
    import csv

class TextNormalizer:
    def __init__(self, name_file, attribute_file, fuzzy_cutoff=85):
        self.fuzzy_cutoff = fuzzy_cutoff
        self.valid_entries = self._load_entries(name_file, attribute_file)
        # self.valid_entries_set = set(self.valid_entries) # sets are O(1) lookup vs O(n) for lists # not hashable so cannot use for lru_cache
        self.replacements = { # used in the case of no match with dictionary (aka text below fuzzy_cutoff OR new data)
            "DUMMYBAD": "DUMMYGOOD",
            "art'$": "art's",
            "art’": "Art",  
            "’": "'",
            "armament' ": "armament's ",
            "armament'": "armament's",
            "armament'$": "armament's",
            "armaments": "armament's",
            "armament s": "armament's",
            "armament'":"armament's",
            "armament'ss":"armament's",
            "armament$":"armament's",
            "Fexpedition": "expedition",
            "Fexpeditions": "expeditions",
            "of. expedition":"of expedition",
            "of, expedition":"of expedition",
            "of = expedition":"of expedition",
            "Endureat":"Endure at",
            "Poison Moth Flightat": "Poison Moth Flight at",
            "landing . critical":"landing a critical",
            "landing : critical":"landing a critical",
            "landing. critical":"landing a critical",
            "etc:":"etc.",
            "Two ~Handing":"Two-Handing",
            "Fability":"ability",
            "shop`":"shop",
            "shop'":"shop",
            "shop-":"shop",
            "'shop":"shop",
            "shop.":"shop",
            "Slecp":"Sleep",
            "Slecp'":"Sleep",
            "slecp":"Sleep",
            "slecp'":"Sleep",
            "'purchases":"purchases",
            "'s $":"'s",
            "'$":"'s",
            "' $":"'s",
            " $":"'s",
            " ' ":" ",
            "[[":"[",
            "i5":"is",
            "+ 1":"+1",
            "+ 3":"+3",
            "Post Damage":"Post-Damage",
            "Post- Damage":"Post-Damage",
            "ofthe":"of the",
            "'ability":"ability",
            "abiliry":"ability",
            "[Revenant ":"[Revenant] ",
        }

        self.debug_log_path = "debug_class_replace_clean.csv"
        if DEBUG:
            with open(self.debug_log_path, "w", newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Raw Input", "Cleaned Input", "Matched Output", "Match Score"])

    @staticmethod
    @lru_cache(maxsize=2048)
    def _normalize_cached(cleaned, valid_entries_tuple, fuzzy_cutoff):
        # exact match first
        valid_entries = list(valid_entries_tuple)
        valid_set = set(valid_entries)
        if cleaned in valid_set:
            return cleaned

        match = process.extractOne(
            cleaned,
            valid_entries,
            processor=None,
            score_cutoff=fuzzy_cutoff
        )
        return match[0] if match else cleaned

    def _load_entries(self, name_file, attribute_file):
        names = self._read_file(name_file)
        attributes = self._read_file(attribute_file)
        return names + attributes

    def _read_file(self, path):
        with open(path, encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]

    def _clean_text(self, text):
        # Apply known replacements
        for bad, good in self.replacements.items():
            text = text.replace(bad, good)
        # General cleanup
        text = re.sub(r'[’‘`]', "'", text)  # normalize apostrophes
        text = re.sub(r'\s{2,}', ' ', text)  # reduce double spaces
        text = re.sub(r"[^\w\s'\":\-+.\(\)\[\]&]", '', text)  # strip garbage (keep these chars)
        text = re.sub(r'\s([:.,])', r'\1', text)
        return text.strip()

    def normalize(self, text):
        raw_input = text
        if not text:
            return ""
        cleaned = self._clean_text(text) # preprocess once instead of per normalize() call
        
        # Non-Cache version
        # # Exact match
        # if cleaned in self.valid_entries_set:
        #     match = cleaned
        # else:   # Fuzzy match
        #     result = process.extractOne(cleaned, self.valid_entries_set, processor=None, score_cutoff=self.fuzzy_cutoff) # default scorer=fuzz.ratio
        #     match = result[0] if result else cleaned

        # Cache-safe: tuple is hashable, list is not
        valid_entries_tuple = tuple(self.valid_entries)
        # match = self._normalize_cached(cleaned, valid_entries_tuple, self.fuzzy_cutoff)

        # Log if debug enabled
        if DEBUG:
            match, score = self._normalize_cached_DEBUG(cleaned, valid_entries_tuple, self.fuzzy_cutoff)
            with open(self.debug_log_path, "a", newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([raw_input, cleaned, match, score])
        else: # not in debug
            match = self._normalize_cached(cleaned, valid_entries_tuple, self.fuzzy_cutoff)

        return match


    @staticmethod
    @lru_cache(maxsize=2048)
    def _normalize_cached_DEBUG(cleaned, valid_entries_tuple, fuzzy_cutoff):
        # exact match first
        valid_entries = list(valid_entries_tuple)
        valid_set = set(valid_entries)
        if cleaned in valid_set:
            return cleaned, 100

        match = process.extractOne(
            cleaned,
            valid_entries,
            processor=None,
            score_cutoff=fuzzy_cutoff
        )
        return (match[0], match[1]) if match else (cleaned, None)