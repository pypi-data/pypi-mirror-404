# -*- coding: utf-8 -*-
"""
Georgian Hyphenation Library v2.2.6
ქართული ენის დამარცვლის ბიბლიოთეკა

Modernized & Optimized
- Hybrid Engine: Algorithm + Dictionary
- Harmonic Clusters Support
- Gemination Handling
- O(1) Cluster Lookup with Set
- Preserves compound word hyphens (v2.2.6)

Author: Guram Zhgamadze
"""

import json
import os
import re
from typing import List, Dict, Set


class GeorgianHyphenator:
    """
    Georgian language hyphenation with hybrid engine
    
    Features:
    - Phonological distance analysis
    - Dictionary-based exception handling
    - Harmonic cluster awareness
    - Gemination (double consonant) handling
    - Anti-orphan protection
    - Preserves compound word hyphens (v2.2.6)
    """
    
    def __init__(self, hyphen_char: str = '\u00AD'):
        """
        Initialize Georgian Hyphenator
        
        Args:
            hyphen_char: Character to use for hyphenation (default: soft hyphen U+00AD)
        """
        self.hyphen_char = hyphen_char
        self.vowels = 'აეიოუ'
        self.left_min = 2
        self.right_min = 2
        
        # v2.2.1: Optimized - Set for O(1) lookup instead of list
        self.harmonic_clusters: Set[str] = {
            'ბლ', 'ბრ', 'ბღ', 'ბზ', 'გდ', 'გლ', 'გმ', 'გნ', 'გვ', 'გზ', 'გრ',
            'დრ', 'თლ', 'თრ', 'თღ', 'კლ', 'კმ', 'კნ', 'კრ', 'კვ', 'მტ', 'პლ', 
            'პრ', 'ჟღ', 'რგ', 'რლ', 'რმ', 'სწ', 'სხ', 'ტკ', 'ტპ', 'ტრ', 'ფლ', 
            'ფრ', 'ფქ', 'ფშ', 'ქლ', 'ქნ', 'ქვ', 'ქრ', 'ღლ', 'ღრ', 'ყლ', 'ყრ', 
            'შთ', 'შპ', 'ჩქ', 'ჩრ', 'ცლ', 'ცნ', 'ცრ', 'ცვ', 'ძგ', 'ძვ', 'ძღ', 
            'წლ', 'წრ', 'წნ', 'წკ', 'ჭკ', 'ჭრ', 'ჭყ', 'ხლ', 'ხმ', 'ხნ', 'ხვ', 'ჯგ'
        }
        
        # v2.2.1: Dictionary for exception words
        self.dictionary: Dict[str, str] = {}
    
    def _strip_hyphens(self, text: str) -> str:
        """
        Remove existing hyphenation symbols (Sanitization)
        
        v2.2.6: Only removes soft hyphens and zero-width spaces,
        preserves regular hyphens for compound words.
        
        Args:
            text: Input text
            
        Returns:
            Text without soft hyphens or zero-width spaces
        """
        if not text:
            return ''
        # v2.2.6: Remove only soft hyphens (\u00AD) and zero-width spaces (\u200B)
        # Preserve regular hyphens (-) for compound words
        text = text.replace('\u00AD', '')  # soft hyphen
        text = text.replace('\u200B', '')  # zero-width space
        
        # Remove custom hyphen_char if it's different from regular hyphen
        if self.hyphen_char not in ['-', '\u00AD']:
            text = text.replace(self.hyphen_char, '')
        
        return text
    
    def load_library(self, data: Dict[str, str]) -> None:
        """
        Load custom dictionary
        
        Args:
            data: Dictionary mapping words to their hyphenation
                  Example: {"საქართველო": "სა-ქარ-თვე-ლო"}
        """
        if data and isinstance(data, dict):
            self.dictionary.update(data)
    
    def load_default_library(self) -> None:
        """
        Load default exceptions dictionary from data/exceptions.json
        
        Works in both development and installed package modes.
        Tries multiple locations to find the data file.
        """
        try:
            package_dir = os.path.dirname(__file__)
            
            # Try multiple possible locations
            locations = [
                # Development mode (root data/ folder)
                os.path.join(package_dir, '..', '..', 'data', 'exceptions.json'),
                # Installed via pip (data/ copied to site-packages)
                os.path.join(os.path.dirname(package_dir), 'data', 'exceptions.json'),
                # Alternative installed location
                os.path.join(package_dir, 'data', 'exceptions.json'),
            ]
            
            data_file = None
            for loc in locations:
                abs_loc = os.path.abspath(loc)
                if os.path.exists(abs_loc):
                    data_file = abs_loc
                    break
            
            if data_file:
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.load_library(data)
                    print(f"Georgian Hyphenation v2.2.6: Dictionary loaded ({len(self.dictionary)} words)")
            else:
                print("Georgian Hyphenation v2.2.6: Dictionary not found, using algorithm only")
        
        except Exception as e:
            print(f"Georgian Hyphenation v2.2.6: Could not load dictionary ({e}), using algorithm only")
    
    def hyphenate(self, word: str) -> str:
        """
        Hyphenate a Georgian word
        
        v2.2.6 Behavior: Strips soft hyphens but preserves regular hyphens
        in compound words.
        
        Args:
            word: Georgian word to hyphenate
            
        Returns:
            Hyphenated word with configured hyphen character
        """
        # v2.2.6: Strip only soft hyphens and zero-width spaces
        sanitized_word = self._strip_hyphens(word)
        
        # Remove punctuation for dictionary lookup (but not hyphens)
        clean_word = re.sub(r'[.,/#!$%^&*;:{}=_`~()]', '', sanitized_word)
        
        # Check dictionary first (if available)
        if clean_word in self.dictionary:
            return self.dictionary[clean_word].replace('-', self.hyphen_char)
        
        # Fallback to algorithm
        return self.apply_algorithm(sanitized_word)
    
    def apply_algorithm(self, word: str) -> str:
        """
        Apply hyphenation algorithm
        
        v2.2.1 Algorithm Features:
        - Vowel-based syllable detection
        - Gemination (double consonant) handling
        - Harmonic cluster preservation
        - Anti-orphan protection (leftMin=2, rightMin=2)
        
        Args:
            word: Word to hyphenate
            
        Returns:
            Hyphenated word
        """
        # Skip short words
        if len(word) < (self.left_min + self.right_min):
            return word
        
        # Find all vowel positions
        vowel_indices = [i for i, char in enumerate(word) if char in self.vowels]
        
        # Need at least 2 vowels for hyphenation
        if len(vowel_indices) < 2:
            return word
        
        insert_points = []
        
        # Analyze each vowel pair
        for i in range(len(vowel_indices) - 1):
            v1 = vowel_indices[i]
            v2 = vowel_indices[i + 1]
            distance = v2 - v1 - 1  # Number of consonants between vowels
            between_substring = word[v1 + 1:v2]
            
            candidate_pos = -1
            
            if distance == 0:
                # V-V: Split between vowels (გა-ა-ნა-ლი-ზა)
                candidate_pos = v1 + 1
            elif distance == 1:
                # V-C-V: Split after vowel (მა-მა)
                candidate_pos = v1 + 1
            else:
                # V-CC...C-V: Complex case
                
                # v2.2.1: Check for gemination (double consonants)
                double_consonant_index = -1
                for j in range(len(between_substring) - 1):
                    if between_substring[j] == between_substring[j + 1]:
                        double_consonant_index = j
                        break
                
                if double_consonant_index != -1:
                    # Split between double consonants (კლას-სი, მას-სა)
                    candidate_pos = v1 + 1 + double_consonant_index + 1
                else:
                    # v2.2.1: Check for harmonic clusters
                    break_index = -1
                    if distance >= 2:
                        last_two = between_substring[distance - 2:distance]
                        if last_two in self.harmonic_clusters:
                            break_index = distance - 2
                    
                    if break_index != -1:
                        # Split before harmonic cluster (ას-ტრო-ნო-მი-ა)
                        candidate_pos = v1 + 1 + break_index
                    else:
                        # Default: split after first consonant (ბარ-ბა-რე)
                        candidate_pos = v1 + 2
            
            # Anti-orphan protection: ensure minimum 2 chars on each side
            if candidate_pos >= self.left_min and (len(word) - candidate_pos) >= self.right_min:
                insert_points.append(candidate_pos)
        
        # Insert hyphens (from right to left to maintain positions)
        result = list(word)
        for pos in reversed(insert_points):
            result.insert(pos, self.hyphen_char)
        
        return ''.join(result)
    
    def get_syllables(self, word: str) -> List[str]:
        """
        Get syllables as a list
        
        Args:
            word: Word to split into syllables
            
        Returns:
            List of syllables without hyphen characters
        """
        hyphenated = self.hyphenate(word)
        return hyphenated.split(self.hyphen_char)
    
    def hyphenate_text(self, text: str) -> str:
        """
        Hyphenate entire Georgian text
        
        Preserves:
        - Punctuation
        - Non-Georgian characters
        - Word boundaries
        - Whitespace
        - Regular hyphens in compound words (v2.2.6)
        
        Args:
            text: Text to hyphenate (can contain multiple words)
            
        Returns:
            Hyphenated text
        """
        if not text:
            return ''
        
        # v2.2.6: Strip only soft hyphens and zero-width spaces
        sanitized_text = self._strip_hyphens(text)
        
        # Split text into Georgian words and other characters
        # Pattern captures Georgian letter sequences
        parts = re.split(r'([ა-ჰ]+)', sanitized_text)
        
        result = []
        for part in parts:
            # Only hyphenate Georgian words with 4+ characters
            if len(part) >= 4 and re.search(r'[ა-ჰ]', part):
                result.append(self.hyphenate(part))
            else:
                result.append(part)
        
        return ''.join(result)


# Convenience functions for backward compatibility and quick usage

def hyphenate(word: str, hyphen_char: str = '\u00AD') -> str:
    """
    Hyphenate a single Georgian word
    
    Args:
        word: Georgian word
        hyphen_char: Hyphen character to use
        
    Returns:
        Hyphenated word
    """
    h = GeorgianHyphenator(hyphen_char)
    return h.hyphenate(word)


def get_syllables(word: str) -> List[str]:
    """
    Get syllables of a Georgian word
    
    Args:
        word: Georgian word
        
    Returns:
        List of syllables
    """
    h = GeorgianHyphenator('-')
    return h.get_syllables(word)


def hyphenate_text(text: str, hyphen_char: str = '\u00AD') -> str:
    """
    Hyphenate Georgian text
    
    Args:
        text: Text containing Georgian words
        hyphen_char: Hyphen character to use
        
    Returns:
        Hyphenated text
    """
    h = GeorgianHyphenator(hyphen_char)
    return h.hyphenate_text(text)


# Export format converters (v2.0 compatibility)

def to_tex_pattern(word: str) -> str:
    """
    Convert to TeX hyphenation pattern format
    
    Args:
        word: Georgian word
        
    Returns:
        TeX pattern (e.g., ".სა1ქარ1თვე1ლო.")
    """
    h = GeorgianHyphenator('-')
    syllables = h.get_syllables(word)
    return '.' + '1'.join(syllables) + '.'


def to_hunspell_format(word: str) -> str:
    """
    Convert to Hunspell hyphenation format
    
    Args:
        word: Georgian word
        
    Returns:
        Hunspell format (e.g., "სა=ქარ=თვე=ლო")
    """
    h = GeorgianHyphenator('-')
    hyphenated = h.hyphenate(word)
    return hyphenated.replace('-', '=')