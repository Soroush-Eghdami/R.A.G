# rag/utils/language_utils.py

import re
from typing import List
from ..config import SUPPORTED_LANGUAGES, PERSIAN_SUPPORT

class LanguageDetector:
    """
    Language detection and processing utilities for multilingual RAG support.
    Supports English, Persian (Farsi), and Arabic.
    """
    
    def __init__(self):
        self.persian_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]')
        self.arabic_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]')
        self.english_pattern = re.compile(r'[a-zA-Z]')
    
    def detect_language(self, text: str) -> str:
        """
        Detect the primary language of the input text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Language code ('en', 'fa', 'ar', or 'mixed')
        """
        if not text or not text.strip():
            return 'en'  # Default to English
        
        # Count characters by script
        persian_chars = len(self.persian_pattern.findall(text))
        arabic_chars = len(self.arabic_pattern.findall(text))
        english_chars = len(self.english_pattern.findall(text))
        
        total_chars = persian_chars + arabic_chars + english_chars
        
        if total_chars == 0:
            return 'en'  # Default to English if no recognizable characters
        
        # Determine primary language
        persian_ratio = persian_chars / total_chars
        arabic_ratio = arabic_chars / total_chars
        english_ratio = english_chars / total_chars
        
        if persian_ratio > 0.3:
            return 'fa'  # Persian
        elif arabic_ratio > 0.3:
            return 'ar'  # Arabic
        elif english_ratio > 0.3:
            return 'en'  # English
        else:
            return 'mixed'  # Mixed languages
    
    def is_persian_text(self, text: str) -> bool:
        """
        Check if text contains Persian characters.
        
        Args:
            text: Text to check
            
        Returns:
            True if text contains Persian characters
        """
        return bool(self.persian_pattern.search(text))
    
    def is_arabic_text(self, text: str) -> bool:
        """
        Check if text contains Arabic characters.
        
        Args:
            text: Text to check
            
        Returns:
            True if text contains Arabic characters
        """
        return bool(self.arabic_pattern.search(text))
    
    def is_rtl_text(self, text: str) -> bool:
        """
        Check if text is right-to-left (Persian/Arabic).
        
        Args:
            text: Text to check
            
        Returns:
            True if text is RTL
        """
        return self.is_persian_text(text) or self.is_arabic_text(text)
    
    def normalize_persian_text(self, text: str) -> str:
        """
        Normalize Persian text for better processing.
        
        Args:
            text: Persian text to normalize
            
        Returns:
            Normalized Persian text
        """
        if not self.is_persian_text(text):
            return text
        
        # Normalize Persian digits to English digits
        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
        english_digits = '0123456789'
        
        for p_digit, e_digit in zip(persian_digits, english_digits):
            text = text.replace(p_digit, e_digit)
        
        # Normalize Persian punctuation
        text = text.replace('،', ',')  # Persian comma
        text = text.replace('؛', ';')  # Persian semicolon
        text = text.replace('؟', '?')  # Persian question mark
        text = text.replace('؛', ';')  # Persian semicolon
        
        return text.strip()
    
    def get_language_prompt_prefix(self, language: str) -> str:
        """
        Get language-specific prompt prefix for better LLM responses.
        
        Args:
            language: Language code
            
        Returns:
            Language-specific prompt prefix
        """
        prefixes = {
            'en': "You are a helpful legal assistant. Answer in English:",
            'fa': "شما یک دستیار حقوقی مفید هستید. به فارسی پاسخ دهید:",
            'ar': "أنت مساعد قانوني مفيد. أجب باللغة العربية:",
            'mixed': "You are a helpful legal assistant. Answer in the same language as the question:"
        }
        
        return prefixes.get(language, prefixes['en'])
    
    def should_use_persian_chunking(self, text: str) -> bool:
        """
        Determine if Persian-specific chunking should be used.
        
        Args:
            text: Text to analyze
            
        Returns:
            True if Persian chunking should be used
        """
        return self.is_persian_text(text) and PERSIAN_SUPPORT

# Global language detector instance
language_detector = LanguageDetector()
