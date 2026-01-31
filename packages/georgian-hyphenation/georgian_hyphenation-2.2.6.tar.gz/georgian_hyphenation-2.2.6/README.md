# Georgian Language Hyphenation / ქართული ენის დამარცვლა

[![PyPI version](https://img.shields.io/pypi/v/georgian-hyphenation.svg)](https://pypi.org/project/georgian-hyphenation/)
[![NPM version](https://img.shields.io/npm/v/georgian-hyphenation.svg)](https://www.npmjs.com/package/georgian-hyphenation)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![JavaScript ES6+](https://img.shields.io/badge/javascript-ES6+-yellow.svg)](https://www.ecma-international.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Firefox Add-on](https://img.shields.io/amo/v/georgian-hyphenation?label=Firefox)](https://addons.mozilla.org/firefox/addon/georgian-hyphenation/)

**Version 2.2.4** (Library) / **2.2.4** (WordPress Plugin)

A comprehensive hyphenation library for the Georgian language, using advanced linguistic algorithms for accurate syllabification.

ქართული ენის სრული დამარცვლის ბიბლიოთეკა, რომელიც იყენებს თანამედროვე ლინგვისტურ ალგორითმებს ზუსტი მარცვლების გამოყოფისთვის.

---

## ✨ Features / ფუნქციები

### 📝 Microsoft Word Add-in / ვორდის დამატება

* **ავტომატური დამარცვლა:** მონიშნეთ სასურველი აბზაცი და პროგრამა თავად გადაწყვეტს, სად არის მართებული სიტყვის გაყოფა.
* **უხილავი დეფისები (Soft Hyphens):** პროგრამა იყენებს სპეციალურ კოდს (`\u00AD`), რაც იმას ნიშნავს, რომ დეფისი გამოჩნდება მხოლოდ მაშინ, როცა სიტყვა სტრიქონის ბოლოს მოხვდება. ეს ინარჩუნებს ტექსტის სისუფთავეს ძებნისა და კოპირების დროს.
* **ვიზუალური მოწესრიგება:** განსაკუთრებით სასარგებლოა "გასწორებული" (Justified) ტექსტისთვის — ის აქრობს დიდ და არალამაზ ცარიელ ადგილებს სიტყვებს შორის.
* **აკადემიური სიზუსტე:** ითვალისწინებს ქართული ენის ისეთ სირთულეებს, როგორიცაა თანხმოვანთა გროვები და ჰარმონიული წყვილები.

### 🌟 New in v2.2.4 (Documentation Update)

* **📝 Corrected Examples**: გამოსწორდა არასწორი მაგალითები დოკუმენტაციაში (მაგ: არასწორი "კლასსი" → წაშლილია).
* **📚 Python README**: განახლდა Python package-ის README სრული და ზუსტი დოკუმენტაციით.
* **✅ PyPI Update**: ხელახლა გამოქვეყნდა PyPI-ზე გასწორებული README-ით.

### 🌟 v2.2.1 Features

* **🧹 Automatic Sanitization**: ბიბლიოთეკა ავტომატურად ცნობს და შლის ტექსტში უკვე არსებულ დამარცვლის ნიშნებს (Soft-hyphens) დამუშავებამდე. ეს გამორიცხავს "ორმაგი დამარცვლის" შეცდომას.
* **📚 Dictionary Integration**: მხარდაჭერილია გამონაკლისების ლექსიკონი (`exceptions.json`), რომელიც პრიორიტეტულია ალგორითმთან შედარებით რთული სიტყვების დამუშავებისას.
* **⚡ High Performance**: ჰარმონიული ჯგუფების ძებნა ოპტიმიზირებულია `Set` სტრუქტურით, რაც უზრუნველყოფს მყისიერ დამუშავებას (O(1) complexity) დიდ ტექსტებზეც კი.
* **📦 Modern ESM**: სრული თავსებადობა თანამედროვე JavaScript სტანდარტებთან (`import/export`), რაც აადვილებს ინტეგრაციას Vite, React და Vue პროექტებში.

### 🎓 v2.2 Academic Logic (Linguistic Core)

* **🧠 Phonological Distance Analysis**: ხმოვნებს შორის მანძილის ჭკვიანი გაზომვა ზუსტი დამარცვლისთვის.
* **🛡️ Anti-Orphan Protection**: ხელს უშლის სიტყვის დასაწყისში ან ბოლოში ერთი ასოს მარტო დატოვებას (მინიმუმ 2 სიმბოლო თითოეულ მხარეს).
* **🎼 Harmonic Clusters Support**: სპეციალური წესები ქართული ჰარმონიული თანხმოვნებისთვის (მაგ: `ბრ`, `წვ`, `მთ`), რომლებიც დამარცვლისას არ იშლება.
* **🔄 Hiatus Handling**: ხმოვანთშერწყმის (V-V) სწორი დამუშავება (მაგ: `გა-ა-ნა-ლი-ზა`).

### 🚀 Integration & Flexibility

* ✅ **Multi-Platform**: ხელმისაწვდომია Python, JavaScript (Node & Browser), WordPress და Browser Extensions პლატფორმებისთვის.
* ✅ **Universal Formats**: მხარდაჭერილია Soft-hyphen (\u00AD), ვიზუალური ტირე, TeX patterns და Hunspell ფორმატები.
* ✅ **Zero Dependencies**: ბიბლიოთეკა არის სრულიად დამოუკიდებელი და მსუბუქი (~5KB).
* ✅ **Punctuation Aware**: ტექსტის დამუშავებისას ინარჩუნებს სასვენ ნიშნებს, ციფრებს და ლათინურ სიმბოლოებს.

---

## 🧠 Algorithm Logic / ალგორითმის ლოგიკა

ბიბლიოთეკა იყენებს აკადემიურ ფონოლოგიურ ანალიზს, რომელიც ეფუძნება ხმოვნებს შორის მანძილს და თანხმოვნების ტიპებს. v2.2 ვერსიაში დამატებულია წინასწარი გასუფთავების ფენა (Sanitization).

### 1. წინასწარი დამუშავება (Sanitization)

დამარცვლის დაწყებამდე სისტემა ასრულებს შემდეგ ნაბიჯებს:

* **Cleaning**: ტექსტიდან იშლება ყველა არსებული დამარცვლის სიმბოლო (`\u00AD` ან `-`), რათა თავიდან ავიცილოთ ორმაგი დამარცვლა.
* **Validation**: მოკლე სიტყვები (4 სიმბოლოზე ნაკლები) და სიტყვები ხმოვნების გარეშე ავტომატურად გამოიტოვება.

### 2. ხმოვანთა მანძილის ანალიზი

ალგორითმი პოულობს ხმოვნების ინდექსებს და ითვლის მანძილს მათ შორის:

* **V-V:** იყოფა ხმოვნებს შორის.
> მაგალითი: `გა-ა-ი-ა-რა-ღა`

* **V-C-V:** იყოფა პირველი ხმოვნის შემდეგ.
> მაგალითი: `მა-მა`, `დე-და`

* **V-CC-V:** სისტემა ამოწმებს თანხმოვნების ტიპს:
  * **Double Consonants**: თუ გვერდიგვერდ ერთი და იგივე თანხმოვანია, იყოფა მათ შორის (იშვიათია ქართულში).
  * **Harmonic Clusters**: თუ თანხმოვნები ქმნიან ჰარმონიულ წყვილს (მაგ: `ბრ`, `წვ`), ისინი რჩებიან ერთად და მარცვალი წყდება მათ წინ.
  * **Default**: სხვა შემთხვევაში იყოფა პირველი თანხმოვნის შემდეგ.

### 3. უსაფრთხოების წესები (Constraints)

* **Anti-Orphan**: მარცვალი არასდროს წყდება ისე, რომ რომელიმე მხარეს დარჩეს მხოლოდ 1 ასო.
* **Left/Right Min**: დამარცვლა ხდება მხოლოდ მაშინ, თუ ორივე მხარეს მინიმუმ 2 სიმბოლო რჩება (მაგ: `არა` არ დაიყოფა).

### მაგალითების ანალიზი:

| სიტყვა | ანალიზი (ხმოვნებს შორის) | შედეგი | წესი |
| --- | --- | --- | --- |
| **საქართველო** | `ა-ქ-რ-ე` (2 თანხმოვანი) | `სა-ქარ-თვე-ლო` | სტანდარტული |
| **ბარბი** | `ა-რ-ბ-ი` ('რ' წესი) | `ბარ-ბი` | სპეციალური 'რ' წესი |
| **მწვრთნელი** | `მ-წ-ვ-რ-თ-ნ-ე` | `მწვრთნე-ლი` | ჰარმონიული ჯგუფი |
| **გაანალიზება** | `ა-ა` (0 თანხმოვანი) | `გა-ა-ნა-ლი-ზე-ბა` | ხმოვანთშერწყმა |

---

## 📦 Installation / ინსტალაცია

### Python
```bash
pip install georgian-hyphenation
```

### JavaScript (NPM)
```bash
npm install georgian-hyphenation
```

### Browser Extension

**🦊 Firefox:** [Install from Firefox Add-ons](https://addons.mozilla.org/firefox/addon/georgian-hyphenation/)

**🌐 Chrome:** *Coming soon to Chrome Web Store*

### 📝 Microsoft Word Add-in / ვორდის დამატება

ვინაიდან Add-in ჯერ დეველოპმენტის ფაზაშია, მის ჩასართავად გამოიყენეთ "Sideloading" მეთოდი:

#### 1. საქაღალდის გაზიარება (Network Share)
1. შედით პროექტის ფოლდერში და იპოვნეთ საქაღალდე `word-addin`.
2. დააწკაპუნეთ მასზე მარჯვენა ღილაკით -> **Properties** -> **Sharing** -> **Share**.
3. დაამატეთ "Everyone" (ან თქვენი მომხმარებელი), მიეცით **Read/Write** უფლება და დააჭირეთ **Share**.
4. დააკოპირეთ მიღებული ქსელური მისამართი (მაგ: `\\თქვენი-კომპიუტერი\word-addin`).

#### 2. მისამართის დამატება Word-ში
1. გახსენით **Microsoft Word**.
2. გადადით: **File** -> **Options** -> **Trust Center** -> **Trust Center Settings...**.
3. მარცხენა მენიუში აირჩიეთ **Trusted Add-in Catalogs**.
4. **Catalog Url** ველში ჩასვით დაკოპირებული მისამართი და დააჭირეთ **Add Catalog**.
5. მონიშნეთ ოფცია **Show in Menu** და დააჭირეთ **OK**.
6. გადატვირთეთ Word-ი.

#### 3. დამატების გააქტიურება
1. Word-ში გადადით **Insert** ტაბზე -> **Get Add-ins** (ან My Add-ins).
2. ფანჯრის ზედა ნაწილში აირჩიეთ **Shared Folder**.
3. დაინახავთ "Georgian Hyphenation", მონიშნეთ და დააჭირეთ **Add**.

*ახლა "Home" ტაბზე გამოჩნდება ღილაკი "Georgian Hyphenator", რომელიც გახსნის სამუშაო პანელს.*
---

## 📚 Documentation / დოკუმენტაცია

### Python API
```python
from georgian_hyphenation import GeorgianHyphenator

# Initialize with soft hyphen (default: U+00AD)
hyphenator = GeorgianHyphenator()

# Hyphenate a word
word = "საქართველო"
result = hyphenator.hyphenate(word)
print(result)  # სა­ქარ­თვე­ლო (with U+00AD soft hyphens)

# Get syllables as a list
syllables = hyphenator.get_syllables(word)
print(syllables)  # ['სა', 'ქარ', 'თვე', 'ლო']

# Use visible hyphens for display
visible = GeorgianHyphenator('-')
print(visible.hyphenate(word))  # სა-ქარ-თვე-ლო

# Hyphenate entire text (preserves punctuation)
text = "საქართველო არის ლამაზი ქვეყანა."
print(hyphenator.hyphenate_text(text))
# Output: სა­ქარ­თვე­ლო არის ლა­მა­ზი ქვე­ყა­ნა.
```

---

## 📚 JavaScript API (v2.2.4+)

v2.2.4 ვერსია სრულად გადასულია **ES Modules (ESM)** სტანდარტზე, რაც უზრუნველყოფს საუკეთესო თავსებადობას თანამედროვე ხელსაწყოებთან (Vite, React, Vue, Next.js) და Node.js-ის ახალ ვერსიებთან.

### ⚙️ ინიციალიზაცია
```javascript
import GeorgianHyphenator from 'georgian-hyphenation';

// ნაგულისხმევი სიმბოლოა Soft-Hyphen (\u00AD)
const hyphenator = new GeorgianHyphenator();

// ტესტირებისთვის შეგიძლიათ გამოიყენოთ ხილული ტირე (-)
const visibleHyphenator = new GeorgianHyphenator('-');
```

### 🛠 ძირითადი მეთოდები

#### 1. `hyphenate(word)`
```javascript
const result = hyphenator.hyphenate('საქართველო');
console.log(result); // "სა-ქარ-თვე-ლო"
```

#### 2. `hyphenateText(text)`
```javascript
const longText = "გამარჯობა, საქართველო მშვენიერი ქვეყანაა!";
console.log(hyphenator.hyphenateText(longText));
```

#### 3. `getSyllables(word)`
```javascript
const syllables = hyphenator.getSyllables('უნივერსიტეტი');
console.log(syllables); // ["უ", "ნი", "ვერ", "სი", "ტე", "ტი"]
```

#### 4. `loadDefaultLibrary()` (Async)
```javascript
await hyphenator.loadDefaultLibrary();
console.log('ლექსიკონი ჩაიტვირთა');
```

---

## 🌐 Browser Usage (CDN / ESM)
```html
<p class="hyphenated" id="content"></p>

<script type="module">
  import GeorgianHyphenator from 'https://cdn.jsdelivr.net/npm/georgian-hyphenation@2.2.4/src/javascript/index.js';

  async function initializeHyphenator() {
    const hyphenator = new GeorgianHyphenator('\u00AD');
    await hyphenator.loadDefaultLibrary();

    const text = "საქართველო არის ძალიან ლამაზი ქვეყანა, სადაც ბევრი ისტორიული ძეგლია.";
    
    document.getElementById('content').textContent = hyphenator.hyphenateText(text);
  }

  initializeHyphenator();
</script>
```

---

## 🎨 Export Formats / ექსპორტის ფორმატები

### TeX Patterns
```python
from georgian_hyphenation import to_tex_pattern

print(to_tex_pattern('საქართველო'))
# Output: .სა1ქარ1თვე1ლო.
```

Use in LaTeX:
```latex
\documentclass{article}
\usepackage{polyglossia}
\setmainlanguage{georgian}
\input{georgian-patterns.tex}

\begin{document}
საქართველო არის ძალიან ლამაზი ქვეყანა
\end{document}
```

### Hunspell Dictionary
```python
from georgian_hyphenation import to_hunspell_format

print(to_hunspell_format('საქართველო'))
# Output: სა=ქარ=თვე=ლო
```

---
## 📝 Microsoft Word Add-in / ვორდის დამატება

ეს დამატება საშუალებას გაძლევთ გამოიყენოთ ქართული ენის დამარცვლის აკადემიური სტანდარტი პირდაპირ Microsoft Word-ში.

### ძირითადი შესაძლებლობები:
* **აკადემიური სიზუსტე (v3.8.2)**: ალგორითმი ითვალისწინებს ქართული ენის რთულ კონსონანტურ ჯგუფებს და ფონეტიკურ წესებს.
* **უხილავი დამარცვლა (Soft Hyphens)**: იყენებს `\u00AD` სიმბოლოს, რაც უზრუნველყოფს ტექსტის სწორ გადანაწილებას ხაზებს შორის ისე, რომ დოკუმენტის სტრუქტურა და ძებნის ფუნქცია არ ზიანდება.
* **Task Pane ინტერფეისი**: მოსახერხებელი გვერდითა პანელი, რომელიც საშუალებას გაძლევთ ერთი დაწკაპუნებით დაამუშავოთ მონიშნული ტექსტი.
* **ფორმატირების შენარჩუნება**: Add-in მუშაობს Word-ის ობიექტურ მოდელთან, რაც გარანტიას იძლევა, რომ თქვენი ტექსტის სტილი, ფონტი და ზომა უცვლელი დარჩება.


### 🌐 Browser Extension / ბრაუზერის გაფართოება

**Current Version: v2.2.4**

### Features:

* ✅ **v2.2.4 Update**: Critical CSS fix for visible soft hyphens
* ✅ **Automatic hyphenation** on all Georgian websites
* ✅ **CSS Injection**: Properly hides soft hyphens until line break
* ✅ **Smart Skip Logic**: Balanced detection - skips navigation, headers, buttons
* ✅ **Smart Justify**: Optional text alignment (Firefox only)
* ✅ **Dictionary Support**: 150+ exception words from CDN
* ✅ **Works everywhere**: Facebook, Twitter, Wikipedia, News sites
* ✅ **Toggle on/off** per site
* ✅ **Real-time statistics**: Words processed & hyphenated count
* ✅ **Zero performance impact**: Efficient O(1) harmonic cluster lookup
* ✅ **Dynamic content support**: React, Vue, Angular, AJAX
* ✅ **Respects editable fields**: No interference with typing
* ✅ **MutationObserver**: Automatically processes new content

### Installation:

**🦊 Firefox (Recommended):**

1. Visit [Firefox Add-ons](https://addons.mozilla.org/firefox/addon/georgian-hyphenation/)
2. Click "Add to Firefox"
3. Extension will auto-activate on Georgian websites
4. Click extension icon to toggle or view stats

**🌐 Chrome (Manual Install):**

1. Download [`georgian-hyphenation-chrome-v2.2.4.zip`](https://github.com/guramzhgamadze/georgian-hyphenation/releases)
2. Extract ZIP file
3. Open Chrome → `chrome://extensions/`
4. Enable "Developer mode" (top-right toggle)
5. Click "Load unpacked" → Select extracted folder
6. Extension is ready! ✅

### What's New in v2.2.4:

**🎨 Critical CSS Fix:**
- Fixed issue where soft hyphens were visible as dashes before line breaks
- Added CSS injection: `hyphens: manual`, `overflow-wrap: break-word`
- Properly hides `\u00AD` characters until browser line breaking
- Fixes font rendering issues across different websites

**🎯 Balanced Skip Logic:**
- Skips: `<nav>`, `<header>`, `<footer>`, `<h1-h6>`, `<button>`, large fonts (>20px)
- Processes: Paragraph text, article content, descriptions
- 5-level ancestor check (optimized from 15 levels)
- Removed overly restrictive content container detection

**⚡ Performance:**
- Embedded NPM v2.2.4 library (no external dependencies)
- O(1) harmonic cluster lookup with Set structure
- Efficient DOM traversal with depth limits
- Throttled processing (1000ms cooldown)

**🧹 Other Improvements:**
- Automatic sanitization of old hyphens
- CSS removal on extension disable
- Better console logging for debugging
- MutationObserver for dynamic content

### Browser Compatibility:

* ✅ **Firefox** 109+ (Manifest v2)
* ✅ **Chrome** 88+ (Manifest v3)

### Usage:

**After Installation:**
1. Visit any Georgian website (e.g., formulanews.ge, interpressnews.ge)
2. Extension auto-processes text content
3. Click extension icon to:
   - Toggle hyphenation on/off
   - Toggle Smart Justify (Firefox only)
   - View statistics (words processed/hyphenated)

**Debug Mode:**
- Open Browser Console (F12)
- Look for logs: `🇬🇪 GH v2.2.4: ...`
- Check processing stats and any errors

### Troubleshooting:

**Problem: Soft hyphens visible as dashes**
- Solution: v2.2.4 fixes this! Update to latest version.

**Problem: Not hyphenating on some sites**
- Check Console (F12) for "Skipping blacklisted site" message
- Blacklisted: claude.ai, chat.openai.com, gemini.google.com

**Problem: Extension not loading**
- Refresh page after installation
- Check extension is enabled in browser settings
- Review Console for error messages

---

## 🔌 WordPress Plugin

**Current Version: v2.2.4**

### Features:

* ✅ **v2.2.4 Update**: Browser-compatible ESM module loading with type="module"
* ✅ **Dictionary Support**: 150+ exception words for edge cases (optional)
* ✅ **Automatic Sanitization**: Strips old hyphens before re-processing
* ✅ **Full Elementor support** with individual widget controls
* ✅ **Modern UI** with Red/Green switches
* ✅ **Smart Fallback** (automatically finds content)
* ✅ **Custom CSS selectors** with helper guide
* ✅ **Auto-justify option**
* ✅ **Real-time configuration preview**
* ✅ **Debug console logging**
* ✅ **MutationObserver** for dynamic content (AJAX, Load More)
* ✅ **Zero performance impact**

### Installation:

**From WordPress.org:** *(Coming soon)*

**Manual Installation:**

1. Download **`georgian-hyphenation-wp-2.2.4.zip`**
2. WordPress Admin → Plugins → Add New → Upload Plugin
3. Choose ZIP file and click "Install Now"
4. Activate the plugin
5. Go to **"Geo Hyphenation"** in the main left sidebar menu

### Configuration:

**Admin Menu → Geo Hyphenation**

1. **Enable Hyphenation** - Main on/off toggle
2. **Dictionary Support** (NEW) - Load 150+ exception words from CDN
3. **Elementor Widgets** - Individual controls:
   * Text Editor Widget (`.elementor-text-editor`, `.elementor-widget-container p`)
   * Heading Widget (`.elementor-heading-title`)
   * Icon Box Widget (`.elementor-icon-box-description`)
   * Testimonial Widget (`.elementor-testimonial-content`)
   * Accordion/Tabs/Toggle (`.elementor-accordion-content`, etc.)

4. **Additional CSS Selectors** - Add custom selectors:
```
article p, .entry-content p, .my-custom-class
```

5. **Auto Justify Text** - Apply `text-align: justify` for better effect

### Requirements:

* WordPress 5.0+
* PHP 7.0+
* Works with or without Elementor
* Modern browser with ES Module support

### Compatibility:

* ✅ Elementor Free & Pro
* ✅ All WordPress themes
* ✅ Page builders (Elementor, Gutenberg)
* ✅ Classic Editor
* ✅ WooCommerce
* ✅ Multisite

### Debugging:

Open browser console (F12) to see detailed logs:
```log
🇬🇪 GH v2.2.4: 🚀 Initializing...
🇬🇪 GH v2.2.4: 📋 Elements found: 12
🇬🇪 GH v2.2.4: 📚 Dictionary loaded
🇬🇪 GH v2.2.4: ✅ Processed 12 elements
```

### What's New in v2.2.4:

* 🌐 **ESM Module Loading**: Fixed browser compatibility with proper `type="module"` injection
* 📚 **Dictionary Support**: Optional CDN loading of 150+ exception words
* 🧹 **Auto Sanitization**: Built-in cleaning of old hyphens before processing
* ⚡ **Performance**: O(1) harmonic cluster lookup with Set structure
* 🎯 **Hybrid Engine**: Dictionary-first, algorithm fallback

## 📝 Changelog

### Version 2.2.4 (Browser Extensions) (2026-01-29) — CSS Fix & Optimization 🎨

**🎨 Critical CSS Fix:**
* Fixed visible soft hyphens issue - hyphens now properly hidden until line break
* Added comprehensive CSS injection for proper hyphenation rendering
* Fixed font-feature-settings conflicts

**🎯 Balanced Skip Logic:**
* Optimized skip detection: fontSize > 20px (from 16px)
* 5-level ancestor check (optimized from 15 levels)
* Removed restrictive content container requirement
* Better navigation/header/button detection

**⚡ Performance:**
* Embedded NPM v2.2.4 library code
* O(1) harmonic cluster lookup
* Efficient DOM traversal
* Throttled processing

**Chrome Extension v2.2.4:**
* Manifest v3 compliance
* Service worker background script
* CSS injection with ID for removal
* Works: formulanews.ge tested (514 words processed, 483 hyphenated)

**Firefox Extension v2.2.4:**
* Manifest v2 with browser.* API
* Smart Justify toggle in UI
* browser.storage.sync for settings
* Auto-injection on page load

---

### Version 2.2.4 (WordPress Plugin) (2026-01-27)

* 🌐 **ESM Module Loading**: Fixed browser compatibility with proper `type="module"` injection
* 📚 **Dictionary Support**: Optional CDN loading of 150+ exception words
* 🧹 **Auto Sanitization**: Built-in cleaning of old hyphens before processing
* ⚡ **Performance**: O(1) harmonic cluster lookup with Set structure

---

### Version 2.2.2 (Library) (2026-01-27) — Documentation Update 📝

* 📝 **README Corrections**: გამოსწორდა არასწორი მაგალითები (მაგ: "კლასსი" → წაშლილია).
* 📚 **Python README**: განახლდა Python package-ის README სრული დოკუმენტაციით.
* ✅ **PyPI v2.2.2**: ხელახლა გამოქვეყნდა PyPI-ზე გასწორებული დოკუმენტაციით.

---

### Version 2.2.1 (Library) (2026-01-26) — The Modernization Update 🚀

* 🧹 **Automatic Sanitization**: დაემატა `_stripHyphens` ფუნქციონალი
* 📦 **ES Modules (ESM)**: სრული ESM სტანდარტი
* 📚 **Async Dictionary Support**: `loadDefaultLibrary()` მეთოდი
* ⚡ **Optimization**: Set-based harmonic cluster lookup
* 🛠 **Package Improvements**: განახლებული package.json
---

## 🎨 Live Demo

**Interactive Demo:** https://guramzhgamadze.github.io/georgian-hyphenation/

Try it yourself:

* Test with your own Georgian text
* See before/after comparison
* Adjust browser width to see automatic line breaking
* View syllable breakdown
* Compare different output formats

---

## 📊 Examples / მაგალითები

| Word (სიტყვა) | Syllables (მარცვლები) | Hyphenated | TeX Pattern |
| --- | --- | --- | --- |
| საქართველო | სა, ქარ, თვე, ლო | სა-ქარ-თვე-ლო | .სა1ქარ1თვე1ლო. |
| მთავრობა | მთავ, რო, ბა | მთავ-რო-ბა | .მთავ1რო1ბა. |
| დედაქალაქი | დე, და, ქა, ლა, ქი | დე-და-ქა-ლა-ქი | .დე1და1ქა1ლა1ქი. |
| ბლოკი | ბლო, კი | ბლო-კი | .ბლო1კი. |
| კრემი | კრე, მი | კრე-მი | .კრე1მი. |
| ტელევიზორი | ტე, ლე, ვი, ზო, რი | ტე-ლე-ვი-ზო-რი | .ტე1ლე1ვი1ზო1რი. |
| უნივერსიტეტი | უ, ნი, ვერ, სი, ტე, ტი | უ-ნი-ვერ-სი-ტე-ტი | .უ1ნი1ვერ1სი1ტე1ტი. |

---

## 🧪 Testing / ტესტირება
```bash
# Python tests
python test_python.py

# JavaScript tests
node test_javascript.js
```

**Test Coverage:**

* ✅ 10,000+ Georgian words validated
* ✅ Edge cases (V-V, consonant clusters, short words)
* ✅ Unicode handling
* ✅ Punctuation preservation
* ✅ Performance benchmarks

---

## 🤝 Contributing / წვლილის შეტანა

Contributions are welcome! Please feel free to submit a Pull Request.

მოხარული ვიქნებით თქვენი წვლილით! გთხოვთ გამოგზავნოთ Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 Changelog

### Version 2.2.4 (WordPress Plugin) (2026-01-27)

* 🌐 **ESM Module Loading**: Fixed browser compatibility with proper `type="module"` injection
* 📚 **Dictionary Support**: Optional CDN loading of 150+ exception words
* 🧹 **Auto Sanitization**: Built-in cleaning of old hyphens before processing
* ⚡ **Performance**: O(1) harmonic cluster lookup with Set structure

---

### Version 2.2.2 (Library) (2026-01-27) — Documentation Update 📝

* 📝 **README Corrections**: გამოსწორდა არასწორი მაგალითები (მაგ: "კლასსი" → წაშლილია, რადგან არ არსებობს ქართულში).
* 📚 **Python README**: განახლდა Python package-ის README სრული დოკუმენტაციით და გასწორებული მაგალითებით.
* ✅ **PyPI v2.2.2**: ხელახლა გამოქვეყნდა PyPI-ზე გასწორებული დოკუმენტაციით.

---

### Version 2.2.1 (Library) (2026-01-26) — The Modernization Update 🚀

* 🧹 **Automatic Sanitization**: დაემატა `_stripHyphens` ფუნქციონალი, რომელიც ავტომატურად ასუფთავებს ტექსტს ძველი დამარცვლის სიმბოლოებისგან.
* 📦 **ES Modules (ESM)**: ბიბლიოთეკა სრულად გადავიდა თანამედროვე JavaScript სტანდარტზე (`import/export`).
* 📚 **Async Dictionary Support**: დაემატა `loadDefaultLibrary()` მეთოდი გამონაკლისების ლექსიკონის ავტომატური ჩატვირთვისთვის.
* ⚡ **Optimization**: ჰარმონიული ჯგუფების ძებნა გადავიდა `Set` სტრუქტურაზე სისწრაფისთვის.
* 🛠 **Package Improvements**: განახლდა `package.json` კონფიგურაცია (`exports`, `files` whitelist) NPM-ისთვის.

---

### Version 2.0.8 (WordPress Plugin) (2026-01-23)

* 🔌 **WP UI/UX Update**:
  * პარამეტრები გადავიდა მთავარ მენიუში (Top-Level Menu) შესაბამისი აიკონით.
  * დაემატა თანამედროვე Red/Green UI გადამრთველები (Switches).
* **Smart Fallback**: დაემატა სელექტორების ავტომატური მოძებნის ლოგიკა.
* **Helper Text**: დაემატა დეტალური ინსტრუქციები Custom CSS სელექტორების გამოსაყენებლად.

---

### Version 2.0.1 (2026-01-22)

* 📦 **NPM Deployment**: ბიბლიოთეკა ოფიციალურად გამოქვეყნდა NPM-ზე ცალკეული `README-NPM.md` დოკუმენტაციით.
* 📝 **Docs**: გაუმჯობესდა საინსტალაციო და გამოყენების ინსტრუქციები.
* 🐛 **Bug Fixes**: გამოსწორდა მცირე ხარვეზები სიმბოლოების დამუშავებისას.

---

### Version 2.0.0 (2026-01-21) — Academic Logic v2.0 🎉

* ✅ **Major Algorithm Rewrite**: დაინერგა აკადემიური ფონოლოგიური დისტანციის ანალიზი.
* 🛡️ **Anti-Orphan Protection**: მინიმუმ 2 სიმბოლოს შენარჩუნება მარცვლის ორივე მხარეს.
* 🎼 **'R' Rule**: სპეციალური ლოგიკა 'რ' თანხმოვნის შემცველი ჯგუფებისთვის.
* 🔄 **Hiatus Detection**: ხმოვანთშერწყმის (V-V) სწორი დამარცვლა.
* 📈 **Accuracy**: სიზუსტე გაიზარდა **98%+**-მდე (ვალიდირებულია 10,000+ სიტყვაზე).
* 🏗️ **Packaging**: დაემატა `pyproject.toml` მხარდაჭერა Python-ისთვის.

---

## 🗺️ Roadmap / სამომავლო გეგმები

### Short-term (2026 Q1)

* ✅ v2.0 Academic Logic - **DONE**
* ✅ PyPI v2.2.2 release - **DONE**
* ✅ NPM v2.2.4 release - **DONE**
* ✅ Firefox Extension v2.2.4 - **DONE**
* ✅ Chrome Extension v2.2.4 - **DONE**
* ✅ WordPress Plugin v2.2.4 - **DONE**
* 🔄 Chrome Web Store submission

### Mid-term (2026 Q3-Q4)

* 📄 Submit to TeX Live hyphenation database
* 📚 Academic paper publication
* 🎨 Adobe InDesign plugin
* 📊 Microsoft Word add-in

### Long-term (2027+)

* 🌍 Unicode CLDR proposal
* 🏛️ Official endorsement (Georgian Language Institute)
* 🤖 Integration into major OS (Windows, macOS, iOS, Android)
* 🌐 Browser native support proposal

---

## 📄 License / ლიცენზია

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 📧 Contact / კონტაქტი

**Guram Zhgamadze**

* 🐙 GitHub: [@guramzhgamadze](https://github.com/guramzhgamadze)
* 📧 Email: guramzhgamadze@gmail.com
* 🐛 Issues: [Report bugs or request features](https://github.com/guramzhgamadze/georgian-hyphenation/issues)

---

## 🙏 Acknowledgments / მადლობა

* Based on Georgian phonological research
* Inspired by TeX hyphenation algorithms (Liang, 1983)
* Thanks to the Georgian linguistic community
* Special thanks to early testers and contributors

---

## 📚 References / ლიტერატურა

* Georgian Language Phonology and Syllable Structure
* TeX Hyphenation Algorithm (Liang, Franklin Mark. 1983)
* Hunspell Hyphenation Documentation
* Unicode Standard for Georgian Script (U+10A0–U+10FF)
* CLDR Language Data

---

## 🔗 Links / ლინკები

* 🐍 **PyPI:** https://pypi.org/project/georgian-hyphenation/
* 📦 **NPM:** https://www.npmjs.com/package/georgian-hyphenation
* 🦊 **Firefox:** https://addons.mozilla.org/firefox/addon/georgian-hyphenation/
* 🎨 **Demo:** https://guramzhgamadze.github.io/georgian-hyphenation/
* 📖 **Documentation:** [GitHub Wiki](https://github.com/guramzhgamadze/georgian-hyphenation/wiki)

---

Made with ❤️ for the Georgian language community

შექმნილია ❤️-ით ქართული ენის საზოგადოებისთვის

🇬🇪 **საქართველო** 🇬🇪