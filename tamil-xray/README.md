# Tamil Content X-Ray — தமிழ் உள்ளடக்க எக்ஸ்-ரே

**AI-Powered Entity Recognition for Tamil Learners**
**DTEC Hackathon 2026 — Student Category**

---

## Project Overview

Tamil Content X-Ray is an AI-powered web application that makes any Tamil text instantly understandable by identifying and explaining every meaningful named entity inside it — in real time, in both Tamil and English.

It solves two critical barriers faced by diaspora Tamil students:
1. **Cultural unfamiliarity** — they don't know who the people, places, and references are inside Tamil text
2. **Script difficulty** — they cannot type in Tamil script (they use Tanglish instead)

---

## Features

| Feature | Description |
|---------|-------------|
| 🔍 Entity Detection | Identifies 9 types of named entities in Tamil text with color highlights |
| 📖 Bilingual Explanation | Student-friendly explanation in both Tamil and English for every entity |
| ✅ Vaani Spellcheck | Pre-processes Tamil text using Tamil Virtual Academy spellcheck engine |
| 🔄 Tanglish Conversion | Type in English letters (Tanglish), get proper Tamil script via AI |
| 📜 Verse Meaning | Full meaning for Tamil poems and multi-line verses |
| ✦ Couplet Meaning | Line-by-line meaning + moral for 2-line classical couplets |
| 📚 Deep Dive | Extended cultural explanation on demand for any entity |
| 🤖 Smart Detection | Automatically detects if input is sentence, paragraph, verse, or couplet |

---

## Entity Types

| Type | Color | Examples |
|------|-------|---------|
| PERSON | 🔵 Blue | கம்பன், திருவள்ளுவர், பாரதியார் |
| PLACE | 🟢 Green | சென்னை, இலங்கை, தமிழ்நாடு |
| ORGANIZATION | 🟠 Orange | அண்ணா பல்கலைக்கழகம், திமுக |
| MYTH | 🔴 Red | இராவணன், அனுமன், முருகன் |
| LITERATURE | 🟣 Purple | திருக்குறள், இராமாயணம், சிலப்பதிகாரம் |
| CULTURAL | 🟡 Yellow | பரதநாட்டியம், கர்னாடக இசை |
| FESTIVAL | 🩷 Pink | பொங்கல், தீபாவளி, தைப்பூசம் |
| FOOD | 💚 Light Green | இட்லி, தோசை, சாம்பார் |
| DYNASTY | 🌸 Magenta | சோழர், பாண்டியர், பல்லவர் |

---

## How It Works

```
User Input (Tamil Script or Tanglish)
            ↓
  [If Tanglish] Gemini AI converts to Tamil Script
            ↓
  Content Type Detection
  (sentence / paragraph / couplet / verse)
            ↓
            ├── Sentence / Paragraph
            │       ↓
            │   Vaani Spellcheck (pre-processing layer)
            │   Corrects everyday spelling mistakes
            │   before AI analysis for better accuracy
            │       ↓
            │   Gemini AI — Entity Recognition (NER)
            │   Identifies all 9 entity types
            │       ↓
            │   Color-highlighted text + bilingual explanations
            │
            └── Couplet / Verse (poem)
                    ↓
                Gemini AI — Meaning Extraction
                Line-by-line meaning + moral + cultural context
                (No entity detection — focus on meaning)
```

---

## About Vaani Integration

This project integrates **Vaani** — the official Tamil spellcheck engine developed by the **Tamil Virtual Academy**, via the open-source `tamilinayavaani` Python package.

**Role of Vaani in this project:**
- Acts as a **pre-processing layer** before AI entity detection
- Corrects common everyday Tamil spelling mistakes in sentences and paragraphs
- Improves entity detection accuracy by ensuring clean input to the AI
- Shows users their spelling mistakes with clear warnings (original → corrected)

**Vaani's limitations (known):**
- Works best for common everyday Tamil words
- Limited coverage for complex verb forms and literary vocabulary
- For proper nouns and literary work names, the AI engine handles understanding directly regardless of minor spelling variations
- Does not run on classical verses/poems — classical Tamil uses archaic grammar that Vaani would incorrectly flag

**This is a known limitation of the Vaani engine itself, not of the integration.**

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3, Flask |
| AI Engine | Google Gemini API (gemini-2.5-flash with multi-model fallback) |
| Spellcheck | Vaani — Tamil Virtual Academy (`tamilinayavaani`) |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Tamil Font | Noto Serif Tamil (Google Fonts) |

---

## Project Structure

```
tamil-xray/
├── app.py              ← Flask backend + AI integration + Vaani spellcheck
├── model.py            ← Gemini AI model configuration and fallback logic
├── requirements.txt    ← Python dependencies
├── README.md           ← This file
└── static/
    └── index.html      ← Complete frontend (HTML + CSS + JS)
```

---

## Setup & Installation

### Requirements
- Python 3.8 or higher
- Google AI Studio API key (free at aistudio.google.com)

### Step 1 — Install dependencies
```bash
pip install -r requirements.txt
pip install tamilinayavaani
```

### Step 2 — Get your Gemini API key
- Visit https://aistudio.google.com
- Sign in with Google account
- Click "Get API Key" → Create new key → Copy it

### Step 3 — Set your API key

**Linux/Mac:**
```bash
export GEMINI_API_KEY="your-api-key-here"
```

**Windows (Command Prompt):**
```cmd
set GEMINI_API_KEY=your-api-key-here
```

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="your-api-key-here"
```

### Step 4 — Run the application
```bash
python app.py
```

### Step 5 — Open in browser
```
http://localhost:5000
```

---

### GitHub Repository

🔗 Source Code: https://github.com/Maleshkumarvelmurugan1982/Tamil-Content-X-Ray-AI-Powered-Entity-Recognition-for-Tamil-Learners

Clone and Run

Step 1 — Clone the repository

bashgit clone https://github.com/Maleshkumarvelmurugan1982/Tamil-Content-X-Ray-AI-Powered-Entity-Recognition-for-Tamil-Learners.git
cd Tamil-Content-X-Ray-AI-Powered-Entity-Recognition-for-Tamil-Learners

Step 2 — Install dependencies

bashpip install -r requirements.txt
pip install tamilinayavaani

Step 3 — Get your free Gemini API key


Visit https://aistudio.google.com
Sign in with Google account
Click Get API Key → Create new key → Copy it


Step 4 — Set your API key

Linux/Mac:

bashexport GEMINI_API_KEY=your-api-key-here

Windows (Command Prompt):

cmdset GEMINI_API_KEY=your-api-key-here

Windows (PowerShell):

powershell$env:GEMINI_API_KEY=your-api-key-here

Step 5 — Run the application

bashpython app.py

Step 6 — Open in browser

http://localhost:5000

## Sample Test Cases

### 1. Sentence — Entity Detection
```
கம்பன் இராமாயணம் எழுதிய போது இலங்கையில் இராவணன் ஆட்சி செய்தான்
```
Expected: PERSON(கம்பன்), LITERATURE(இராமாயணம்), PLACE(இலங்கை), MYTH(இராவணன்)

### 2. Sentence — All Entity Types
```
சோழர்கள் தஞ்சாவூரில் பொங்கல் திருவிழா கொண்டாடி பரதநாட்டியம் ஆடினார்கள்
```
Expected: DYNASTY, PLACE, FESTIVAL, CULTURAL

### 3. Paragraph — Vaani + Entities
```
சுப்பிரமணிய பாரதியார் சென்னையில் வாழ்ந்து இந்தியாவிற்காக சுதந்திரப் பாடல்கள் எழுதினார். தமிழ்நாடு அரசு அவரது பாடல்களை பாடசாலைகளில் கற்பிக்கிறது.
```

### 4. Thirukkural — 2-line Couplet
```
அகர முதல எழுத்தெல்லாம் ஆதி
பகவன் முதற்றே உலகு
```
Expected: Full meaning + line-by-line + moral

### 5. Purananuru — 2-line Couplet
```
யாதும் ஊரே யாவரும் கேளிர்
தீதும் நன்றும் பிறர்தர வாரா
```
Expected: Full meaning + line-by-line + moral

### 6. Bharathiyar — Verse
```
அச்சமில்லை அச்சமில்லை அச்சமென்பதில்லையே
இச்சகத்துளோரெல்லாம் எதிர்த்து நின்ற போதினும்
அச்சமில்லை அச்சமில்லை அச்சமென்பதில்லையே
```
Expected: Full meaning + line-by-line + cultural context

### 7. Sangam Poem — 5 Lines
```
யாயும் ஞாயும் யாரா கியரோ
எந்தையும் நுந்தையும் எம்முறைக் கேளிர்
யானும் நீயும் எவ்வழி யறிதும்
செம்புலப் பெயனீர் போல
அன்புடை நெஞ்சம் தாங்கலந் தனவே
```

### 8. Tanglish Input (switch to Tanglish mode first)
```
kamban ramayanam ezhuthiyavar illangaiyil raavanan aatchi seithaan
```
Expected: Converts to Tamil → entity detection

### 9. Single Line Couplet (AI detection test)
```
அகர முதல எழுத்தெல்லாம் ஆதி பகவன் முதற்றே உலகு
```
Expected: Detected as couplet even in single line

### 10. Vaani Spelling Mistake Detection
```
திருவள்ளுவர் திருக்குரல் எழுதினார் தமிழ்நாட்டில் பிரபலமானது
```
Expected: Vaani warns spelling mistake + entity detection

---

## Important Notes for Reviewers

1. **API Key required:** The app needs a Google Gemini API key to run. Get one free at aistudio.google.com
2. **Internet connection:** Required for Gemini API calls
3. **Vaani spellcheck:** Works for common Tamil words. Literary proper nouns may not be caught — this is a known Vaani engine limitation
4. **Model fallback:** The app automatically tries 16 different Gemini models if one is unavailable, ensuring reliability
5. **Classical verses:** Vaani is intentionally disabled for verses and poems to avoid incorrect flagging of classical Tamil grammar

---

## Real Impact

- A 10-year-old in Canada can paste a Thirukkural verse and understand every reference
- A teenager in the UK can type Tanglish and receive full cultural context instantly
- A teacher in the USA can bring classical Tamil literature alive in their classroom in seconds

---

## Team

**Project Title:** Tamil Content X-Ray — AI-Powered Entity Recognition for Tamil Learners
**Topic:** Entity Recognition for Tamil Contents
**Category:** Student
**Event:** DTEC Hackathon 2026

---

*தமிழ் — உலகின் பழமையான செம்மொழி*
*Tamil — The oldest classical language in the world*

---

## Submission Details

| Field | Details |
|-------|---------|
| **Email Address** | malesh26032006@gmail.com |
| **First Name** | Maleshkumar |
| **Last Name** | V |
| **Hackathon Title** | Tamil Content X-Ray — AI-Powered Entity Recognition for Tamil Learners |

