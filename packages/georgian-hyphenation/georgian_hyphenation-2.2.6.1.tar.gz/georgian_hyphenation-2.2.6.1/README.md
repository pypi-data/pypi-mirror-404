# Georgian Hyphenation

[![PyPI version](https://img.shields.io/pypi/v/georgian-hyphenation.svg)](https://pypi.org/project/georgian-hyphenation/)
[![Python versions](https://img.shields.io/pypi/pyversions/georgian-hyphenation.svg)](https://pypi.org/project/georgian-hyphenation/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Georgian Language Hyphenation Library - Fast, accurate syllabification for Georgian (ქართული) text with support for Python 3.7+.

## Features

- ✅ **Accurate Georgian syllabification** based on phonetic rules
- ✅ **Harmonic consonant clusters** recognition (ბრ, გრ, კრ, etc.)
- ✅ **Gemination handling** (double consonant splitting)
- ✅ **Exception dictionary** for irregular words
- ✅ **Preserves compound word hyphens** (new in v2.2.5)
- ✅ **Zero dependencies**
- ✅ **Lightweight** and fast
- ✅ **Type hints** for better IDE support

## Installation
```bash
pip install georgian-hyphenation
```

## Quick Start
```python
from georgian_hyphenation import GeorgianHyphenator

# Create hyphenator instance
hyphenator = GeorgianHyphenator()

# Hyphenate a word
result = hyphenator.hyphenate('საქართველო')
print(result)  # სა­ქარ­თვე­ლო

# Get syllables as a list
syllables = hyphenator.get_syllables('თბილისი')
print(syllables)  # ['თბი', 'ლი', 'სი']

# Hyphenate entire text
text = 'საქართველო არის ძალიან ლამაზი ქვეყანა'
hyphenated = hyphenator.hyphenate_text(text)
print(hyphenated)
```

## Usage

### Basic Hyphenation
```python
from georgian_hyphenation import GeorgianHyphenator

hyphenator = GeorgianHyphenator()

# Single word
print(hyphenator.hyphenate('კომპიუტერი'))
# Output: კომ­პი­უ­ტე­რი

# Multiple words
print(hyphenator.hyphenate_text('პროგრამირება არის შემოქმედება'))
# Output: პრო­გრა­მი­რე­ბა არის შე­მოქ­მე­დე­ბა
```

### Custom Hyphen Character
```python
# Use visible hyphen instead of soft hyphen
hyphenator = GeorgianHyphenator(hyphen_char='-')
print(hyphenator.hyphenate('საქართველო'))
# Output: სა-ქარ-თვე-ლო

# Use custom separator
hyphenator = GeorgianHyphenator(hyphen_char='•')
print(hyphenator.hyphenate('საქართველო'))
# Output: სა•ქარ•თვე•ლო
```

### Get Syllables as List
```python
hyphenator = GeorgianHyphenator()

syllables = hyphenator.get_syllables('განათლება')
print(syllables)  # ['გა', 'ნათ', 'ლე', 'ბა']

# Count syllables
word = 'უნივერსიტეტი'
syllable_count = len(hyphenator.get_syllables(word))
print(f'{word} has {syllable_count} syllables')
```

### Custom Dictionary
```python
hyphenator = GeorgianHyphenator()

# Add custom hyphenation patterns
custom_words = {
    'განათლება': 'გა-ნათ-ლე-ბა',
    'უნივერსიტეტი': 'უ-ნი-ვერ-სი-ტე-ტი'
}

hyphenator.load_library(custom_words)

print(hyphenator.hyphenate('განათლება'))
# Uses your custom pattern
```

### Load Default Dictionary
```python
hyphenator = GeorgianHyphenator()

# Load built-in exception dictionary
hyphenator.load_default_library()

# Now hyphenator will use dictionary for common words
# and fall back to algorithm for unknown words
```

### Compound Words (v2.2.5+)

The library now preserves existing hyphens in compound words:
```python
hyphenator = GeorgianHyphenator()

# Compound words keep their hyphens
print(hyphenator.hyphenate('მაგ-რამ'))
# Output: მაგ-რამ (hyphen preserved)

print(hyphenator.hyphenate('ხელ-ფეხი'))
# Output: ხელ-ფეხი (hyphen preserved)
```

## Convenience Functions

For quick one-off usage without creating an instance:
```python
from georgian_hyphenation import hyphenate, get_syllables, hyphenate_text

# Quick hyphenation
print(hyphenate('საქართველო'))

# Quick syllable extraction
print(get_syllables('თბილისი'))

# Quick text hyphenation
print(hyphenate_text('ეს არის ტექსტი'))
```

## Export Formats

### TeX Pattern Format
```python
from georgian_hyphenation import to_tex_pattern

pattern = to_tex_pattern('საქართველო')
print(pattern)  # .სა1ქარ1თვე1ლო.
```

### Hunspell Format
```python
from georgian_hyphenation import to_hunspell_format

hunspell = to_hunspell_format('საქართველო')
print(hunspell)  # სა=ქარ=თვე=ლო
```

## Algorithm

The library uses a sophisticated phonetic algorithm based on Georgian syllable structure:

### Rules Applied:

1. **Vowel Detection**: Identifies Georgian vowels (ა, ე, ი, ო, უ)
2. **Consonant Cluster Analysis**: Recognizes 70+ harmonic clusters
3. **Gemination Rules**: Splits double consonants (კკ → კ­კ)
4. **Orphan Prevention**: Ensures minimum syllable length (2 characters on each side)

### Supported Harmonic Clusters:
```
ბლ, ბრ, ბღ, ბზ, გდ, გლ, გმ, გნ, გვ, გზ, გრ, დრ, თლ, თრ, თღ, 
კლ, კმ, კნ, კრ, კვ, მტ, პლ, პრ, ჟღ, რგ, რლ, რმ, სწ, სხ, ტკ, 
ტპ, ტრ, ფლ, ფრ, ფქ, ფშ, ქლ, ქნ, ქვ, ქრ, ღლ, ღრ, ყლ, ყრ, შთ, 
შპ, ჩქ, ჩრ, ცლ, ცნ, ცრ, ცვ, ძგ, ძვ, ძღ, წლ, წრ, წნ, წკ, ჭკ, 
ჭრ, ჭყ, ხლ, ხმ, ხნ, ხვ, ჯგ
```

### Syllable Patterns:

- **V-V**: Split between vowels (გა­ა­ნა­ლი­ზა)
- **V-C-V**: Split after first vowel (მა­მა)
- **V-CC-V**: Split between consonants (ბარ­ბა­რე)
- **V-ხრ-V**: Keep harmonic clusters together (ას­ტრო­ნო­მი­ა)
- **V-კკ-V**: Split gemination (კლას­სი)

## API Reference

### `GeorgianHyphenator(hyphen_char='\u00AD')`

Main hyphenator class.

**Parameters:**
- `hyphen_char` (str): Character to use for hyphenation. Default is soft hyphen (U+00AD)

**Methods:**

#### `hyphenate(word: str) -> str`
Hyphenate a single Georgian word.

#### `get_syllables(word: str) -> List[str]`
Get syllables as a list without hyphen characters.

#### `hyphenate_text(text: str) -> str`
Hyphenate all Georgian words in text, preserving punctuation and spacing.

#### `load_library(data: Dict[str, str]) -> None`
Load custom dictionary mapping words to their hyphenation patterns.

#### `load_default_library() -> None`
Load built-in exception dictionary for common irregular words.

#### `apply_algorithm(word: str) -> str`
Apply the hyphenation algorithm directly (used internally).

### Convenience Functions
```python
hyphenate(word: str, hyphen_char: str = '\u00AD') -> str
get_syllables(word: str) -> List[str]
hyphenate_text(text: str, hyphen_char: str = '\u00AD') -> str
to_tex_pattern(word: str) -> str
to_hunspell_format(word: str) -> str
```

## Performance

- **Speed**: ~0.05ms per word on average
- **Memory**: ~50KB with dictionary loaded
- **Optimization**: Uses `Set` for O(1) cluster lookups

## Examples

### Text Processing Pipeline
```python
from georgian_hyphenation import GeorgianHyphenator

hyphenator = GeorgianHyphenator()
hyphenator.load_default_library()

def process_document(text):
    """Process Georgian document for web display"""
    return hyphenator.hyphenate_text(text)

# Use in your application
article = """
საქართველო არის ერთ-ერთი უძველესი ქვეყანა მსოფლიოში.
თბილისი არის დედაქალაქი და კულტურული ცენტრი.
"""

processed = process_document(article)
```

### E-book Generator
```python
from georgian_hyphenation import GeorgianHyphenator

def format_for_ebook(paragraphs):
    hyphenator = GeorgianHyphenator('\u00AD')  # soft hyphen
    hyphenator.load_default_library()
    
    formatted = []
    for paragraph in paragraphs:
        formatted.append(hyphenator.hyphenate_text(paragraph))
    
    return '\n\n'.join(formatted)
```

### Syllable Counter
```python
from georgian_hyphenation import get_syllables

def count_syllables_in_text(text):
    words = text.split()
    total = 0
    for word in words:
        # Remove punctuation
        clean_word = ''.join(c for c in word if c.isalpha())
        if clean_word:
            syllables = get_syllables(clean_word)
            total += len(syllables)
    return total

text = "საქართველო არის ლამაზი ქვეყანა"
print(f"Total syllables: {count_syllables_in_text(text)}")
```

### Poetry Analyzer
```python
from georgian_hyphenation import GeorgianHyphenator

def analyze_verse(line):
    """Analyze syllable structure of Georgian poetry"""
    hyphenator = GeorgianHyphenator('-')
    words = line.split()
    
    analysis = []
    for word in words:
        syllables = hyphenator.get_syllables(word)
        analysis.append({
            'word': word,
            'syllables': syllables,
            'count': len(syllables)
        })
    
    return analysis

verse = "მთვარე ანათებს ცისკარზე"
print(analyze_verse(verse))
```

## Testing
```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

## Changelog

### v2.2.5 (2026-01-30)
- ✨ **New**: Preserves regular hyphens in compound words
- 🐛 **Fixed**: Hyphen stripping now only removes soft hyphens and zero-width spaces
- 📝 **Improved**: Documentation and examples
- 🔧 **Changed**: `_strip_hyphens()` method behavior

### v2.2.2
- Dictionary support added
- Performance optimizations with Set-based lookups

### v2.2.1
- Hybrid engine (Algorithm + Dictionary)
- Harmonic cluster support
- Gemination handling

### v2.0.0
- Complete rewrite with academic phonological rules
- Anti-orphan protection
- Type hints added

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT © [Guram Zhgamadze](https://github.com/guramzhgamadze)

## Author

**Guram Zhgamadze**
- GitHub: [@guramzhgamadze](https://github.com/guramzhgamadze)
- Email: guramzhgamadze@gmail.com

## Related Projects

- [georgian-hyphenation (npm)](https://www.npmjs.com/package/georgian-hyphenation) - JavaScript/Node.js version
- [Georgian Language Resources](https://www.omniglot.com/writing/georgian.htm)
- [Unicode Georgian Range](https://unicode.org/charts/PDF/U10A0.pdf)

## Citation

If you use this library in academic work, please cite:
```bibtex
@software{georgian_hyphenation,
  author = {Zhgamadze, Guram},
  title = {Georgian Hyphenation Library},
  year = {2024},
  publisher = {GitHub},
  url = {https://github.com/guramzhgamadze/georgian-hyphenation}
}
```

## Acknowledgments

- Based on Georgian phonological and syllabification rules
- Inspired by traditional Georgian typography standards
- Community feedback and contributions

---

Made with ❤️ for the Georgian language community

**ქართული ენის თანამშრომლობისთვის**