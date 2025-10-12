"""
Text Preprocessing Utilities for NLP Tasks

This module provides functions to clean and preprocess text for Named Entity Recognition
and employee name detection, specifically handling cases where greeting words or question
words are attached to names without proper spacing.
"""

import re
from typing import List, Tuple, Optional

# Try to import spaCy, but make it optional
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    spacy = None

class TextPreprocessor:
    """
    Text preprocessor for NLP tasks with focus on employee name detection
    """
    
    def __init__(self):
        # Common greeting words that might be attached to names
        self.greeting_words = [
            'hello', 'hi', 'hey', 'hiya', 'greetings', 'good', 'morning', 
            'afternoon', 'evening', 'welcome', 'dear'
        ]
        
        # Question words that might be attached to names
        self.question_words = [
            'what', 'who', 'where', 'when', 'why', 'how', 'which', 'whose',
            'can', 'could', 'would', 'should', 'will', 'do', 'does', 'did',
            'is', 'are', 'was', 'were', 'have', 'has', 'had'
        ]
        
        # Common prepositions and articles that might be attached
        self.function_words = [
            'the', 'a', 'an', 'of', 'to', 'for', 'with', 'by', 'from', 'about',
            'give', 'show', 'tell', 'get', 'please', 'thanks'
        ]
        
        # Combine all words that should be separated
        self.separator_words = self.greeting_words + self.question_words + self.function_words
        
        # Try to load spaCy model, fallback to regex if not available
        self.nlp = None
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                print("Warning: spaCy English model not found. Using regex-based approach.")
        else:
            print("Info: spaCy not installed. Using regex-based approach.")
    
    def separate_attached_words(self, text: str) -> str:
        """
        Main function to separate greeting/question words from names
        
        Args:
            text (str): Input text that may contain attached words
            
        Returns:
            str: Cleaned text with proper spacing
        """
        if not text or not isinstance(text, str):
            return text
        
        # First, try spaCy-based approach if available
        if self.nlp:
            cleaned_text = self._separate_with_spacy(text)
        else:
            cleaned_text = text
        
        # Apply regex-based separation for common patterns
        cleaned_text = self._separate_with_regex(cleaned_text)
        
        # Clean up extra whitespace
        cleaned_text = self._clean_whitespace(cleaned_text)
        
        return cleaned_text
    
    def _separate_with_spacy(self, text: str) -> str:
        """
        Use spaCy tokenization to help identify word boundaries
        """
        try:
            doc = self.nlp(text)
            tokens = []
            
            for token in doc:
                # Check if this token contains multiple words stuck together
                separated = self._check_for_attached_words(token.text)
                tokens.append(separated)
            
            return ' '.join(tokens)
        except Exception as e:
            print(f"spaCy processing failed: {e}")
            return text
    
    def _separate_with_regex(self, text: str) -> str:
        """
        Use regex patterns to separate attached words while preserving case
        """
        # Handle specific common patterns more precisely
        # Pattern: HelloJohn, HiAli, etc. - greeting + capitalized name
        for greeting in ['hello', 'hi', 'hey', 'hiya']:
            # Case insensitive matching but preserve original case in replacement
            pattern = rf'\b({greeting})([A-Z][a-zA-Z]+)\b'
            def replace_func(match):
                return f"{match.group(1)} {match.group(2)}"
            text = re.sub(pattern, replace_func, text, flags=re.IGNORECASE)
        
        # Pattern: WhatJohn, WhoAli, etc. - question word + capitalized name
        for question in ['what', 'who', 'where', 'when', 'why', 'how', 'which']:
            pattern = rf'\b({question})([A-Z][a-zA-Z]+)\b'
            def replace_func(match):
                return f"{match.group(1)} {match.group(2)}"
            text = re.sub(pattern, replace_func, text, flags=re.IGNORECASE)
        
        # Pattern: CanJohn, CouldAli, etc. - modal verb + capitalized name
        for modal in ['can', 'could', 'would', 'should', 'will', 'may', 'might']:
            pattern = rf'\b({modal})([A-Z][a-zA-Z]+)\b'
            def replace_func(match):
                return f"{match.group(1)} {match.group(2)}"
            text = re.sub(pattern, replace_func, text, flags=re.IGNORECASE)
        
        # Pattern: GiveJohn, ShowAli, etc. - action verb + capitalized name
        for verb in ['give', 'show', 'tell', 'get', 'find', 'see']:
            pattern = rf'\b({verb})([A-Z][a-zA-Z]+)\b'
            def replace_func(match):
                return f"{match.group(1)} {match.group(2)}"
            text = re.sub(pattern, replace_func, text, flags=re.IGNORECASE)
        
        # Pattern: AboutJohn, ForAli, etc. - preposition + capitalized name
        for prep in ['about', 'for', 'with', 'from', 'to']:
            pattern = rf'\b({prep})([A-Z][a-zA-Z]+)\b'
            def replace_func(match):
                return f"{match.group(1)} {match.group(2)}"
            text = re.sub(pattern, replace_func, text, flags=re.IGNORECASE)
        
        return text
    
    def _check_for_attached_words(self, token: str) -> str:
        """
        Check if a token contains attached words and separate them
        """
        if len(token) < 4:  # Too short to contain attached words
            return token
        
        # Check each separator word
        for word in self.separator_words:
            # Case 1: word + Name (e.g., "HelloJohn")
            if token.lower().startswith(word.lower()) and len(token) > len(word):
                remainder = token[len(word):]
                if remainder and remainder[0].isupper():
                    return f"{token[:len(word)]} {remainder}"
            
            # Case 2: Name + word (e.g., "JohnHello") - less common but possible
            if token.lower().endswith(word.lower()) and len(token) > len(word):
                prefix = token[:-len(word)]
                if prefix and prefix[0].isupper():
                    return f"{prefix} {token[-len(word):]}"
        
        return token
    
    def _clean_whitespace(self, text: str) -> str:
        """
        Clean up extra whitespace while preserving original structure
        """
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def extract_employee_names(self, text: str) -> List[str]:
        """
        Extract potential employee names from preprocessed text
        
        Args:
            text (str): Preprocessed text
            
        Returns:
            List[str]: List of potential employee names
        """
        # First preprocess the text
        cleaned_text = self.separate_attached_words(text)
        
        # Known employee names for validation - get from CRM dynamically
        try:
            from core.crm.real_crm_server import get_all_employees
            employees = get_all_employees()
            known_employees = set()
            
            if employees:
                for emp in employees:
                    if emp.get('firstname'):
                        known_employees.add(self._normalize_turkish(emp['firstname']).lower())
                        known_employees.add(emp['firstname'].lower())
                    if emp.get('lastname'):
                        known_employees.add(self._normalize_turkish(emp['lastname']).lower())
                        known_employees.add(emp['lastname'].lower())
        except Exception as e:
            print(f"Warning: Could not fetch employee names from CRM: {e}")
            # Fallback to hardcoded list with Turkish names
            known_employees = {
                'hamza', 'nawaz', 'deniz', 'john', 'sarah', 'alex', 'maria',
                'ahmed', 'ali', 'omar', 'fatima', 'zara', 'hassan', 'aisha',
                'ilahe', 'İlahe', 'tugba', 'tuğba', 'begum', 'begüm', 'gulay', 'gülay',
                'ihsan', 'İhsan', 'yusuf', 'ziya', 'saygi', 'saygı', 'damla', 'ustundag', 'üstündağ',
                'calikoglu', 'çalıkoğlu', 'sen', 'şen', 'sencer', 'şencer', 'keskin'
            }
        
        # Words to exclude from being considered names
        excluded_words = set(self.separator_words + [
            'tasks', 'performance', 'report', 'analysis', 'productivity',
            'overdue', 'completed', 'progress', 'status', 'working'
        ])
        
        names = []
        words = cleaned_text.split()
        
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word).lower()
            normalized_word = self._normalize_turkish(clean_word)
            
            # Skip if it's an excluded word
            if clean_word in excluded_words or normalized_word in excluded_words:
                continue
            
            # Check if it's a known employee name (both original and normalized)
            if clean_word in known_employees or normalized_word in known_employees:
                names.append(word.strip('.,!?:;'))
                continue
            
            # Check if it looks like a proper name (supports Turkish characters)
            if (self._is_turkish_name_like(word) and 
                len(word) >= 3 and len(word) <= 15 and 
                clean_word not in excluded_words and
                normalized_word not in excluded_words):
                names.append(word.strip('.,!?:;'))
        
        return list(set(names))  # Remove duplicates

    def _normalize_turkish(self, text: str) -> str:
        """Normalize Turkish characters to basic Latin characters"""
        if not text:
            return ""
        
        # Turkish character mappings
        turkish_chars = {
            'İ': 'I', 'ı': 'i', 'Ğ': 'G', 'ğ': 'g', 'Ü': 'U', 'ü': 'u',
            'Ş': 'S', 'ş': 's', 'Ö': 'O', 'ö': 'o', 'Ç': 'C', 'ç': 'c'
        }
        
        result = text
        for turkish_char, latin_char in turkish_chars.items():
            result = result.replace(turkish_char, latin_char)
        
        return result

    def _is_turkish_name_like(self, word: str) -> bool:
        """Check if a word looks like a Turkish name (supports Turkish characters)"""
        if not word:
            return False
        
        # Check if first character is uppercase (Turkish or Latin)
        if not (word[0].isupper() or word[0] in 'İĞÜŞÖÇ'):
            return False
        
        # Check if all characters are alphabetic (including Turkish characters)
        turkish_chars = set('İıĞğÜüŞşÖöÇç')
        for char in word:
            if not (char.isalpha() or char in turkish_chars):
                return False
        
        return True


def test_text_preprocessor():
    """
    Test function to verify the text preprocessor works correctly
    """
    preprocessor = TextPreprocessor()
    
    test_cases = [
        # Basic attached greetings
        ("HelloJohn", "Hello John"),
        ("HiAli", "Hi Ali"),
        ("HeyMaria", "Hey Maria"),
        
        # Attached question words
        ("WhatAli", "What Ali"),
        ("WhoJohn", "Who John"),
        ("WhereHamza", "Where Hamza"),
        ("HowSarah", "How Sarah"),
        
        # Attached function words
        ("GiveHamza", "Give Hamza"),
        ("ShowNawaz", "Show Nawaz"),
        ("TellDeniz", "Tell Deniz"),
        ("CanAlex", "Can Alex"),
        ("CouldMaria", "Could Maria"),
        
        # Multiple attached words
        ("HelloGiveJohn", "Hello Give John"),
        ("WhatAboutAli", "What About Ali"),
        
        # Normal text (should remain unchanged)
        ("Hello John", "Hello John"),
        ("Give me Hamza report", "Give me Hamza report"),
        ("What about Ali's tasks", "What about Ali's tasks"),
        
        # Mixed cases
        ("HelloJohn how are you", "Hello John how are you"),
        ("Please ShowHamza performance", "Please Show Hamza performance"),
        ("WhatAli overdue tasks", "What Ali overdue tasks"),
        
        # Edge cases
        ("Hi", "Hi"),
        ("John", "John"),
        ("", ""),
        ("HELLO", "HELLO"),
    ]
    
    print("Testing Text Preprocessor:")
    print("=" * 50)
    
    for i, (input_text, expected) in enumerate(test_cases, 1):
        result = preprocessor.separate_attached_words(input_text)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        
        print(f"Test {i:2d}: {status}")
        print(f"  Input:    '{input_text}'")
        print(f"  Expected: '{expected}'")
        print(f"  Got:      '{result}'")
        
        if result != expected:
            print(f"  ⚠️  MISMATCH!")
        print()
    
    # Test name extraction
    print("Testing Name Extraction:")
    print("=" * 30)
    
    name_test_cases = [
        "HelloJohn please show tasks",
        "WhatAli performance report", 
        "Give me Hamza overdue tasks",
        "ShowNawaz current status",
        "How is Sarah doing",
    ]
    
    for text in name_test_cases:
        names = preprocessor.extract_employee_names(text)
        print(f"Text: '{text}'")
        print(f"Extracted names: {names}")
        print()


if __name__ == "__main__":
    test_text_preprocessor()