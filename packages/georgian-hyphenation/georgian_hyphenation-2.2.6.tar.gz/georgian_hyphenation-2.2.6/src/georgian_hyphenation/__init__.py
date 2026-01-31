# -*- coding: utf-8 -*-
"""
Georgian Language Hyphenation Library
ქართული ენის დამარცვლის ბიბლიოთეკა
Version: 2.2.6
"""
from .hyphenator import (
    GeorgianHyphenator,
    hyphenate,
    get_syllables,
    hyphenate_text,
    to_tex_pattern,
    to_hunspell_format
)
__version__ = '2.2.6'
__author__ = 'Guram Zhgamadze'
__all__ = [
    'GeorgianHyphenator',
    'hyphenate',
    'get_syllables',
    'hyphenate_text',
    'to_tex_pattern',
    'to_hunspell_format'
]