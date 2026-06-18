"""
Tamil Content X-Ray — Backend Server
Uses Google Gemini API with automatic fallback across all available models
"""

import os
import sys
import json
import re
import time
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from google import genai

sys.path.insert(0, '/usr/local/lib/python3.12/dist-packages')
try:
    from tamilinayavaani import SpellChecker as VaaniChecker
    VAANI_AVAILABLE = True
    print("✅ Vaani spellcheck engine loaded")
except ImportError:
    VAANI_AVAILABLE = False
    print("⚠️  Vaani not available")

app = Flask(__name__, static_folder="static")
CORS(app)

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# All available text generation models — lightest/fastest first
MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash-lite-001",
    "gemini-2.0-flash",
    "gemini-2.0-flash-001",
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite-preview",
    "gemini-flash-lite-latest",
    "gemini-flash-latest",
    "gemini-2.5-flash",
    "gemini-3.1-pro-preview",
    "gemini-3-pro-preview",
    "gemini-2.5-pro",
    "gemini-pro-latest",
]

def generate(prompt):
    """Try every model, retry 3x each with wait on 503."""
    last_error = None
    for model in MODELS:
        for attempt in range(3):
            try:
                response = client.models.generate_content(model=model, contents=prompt)
                print(f"✅ Success with model: {model}")
                return response.text.strip()
            except Exception as e:
                err = str(e)
                print(f"⚠️  {model} attempt {attempt+1} failed: {err[:80]}")
                last_error = e
                if "503" in err or "UNAVAILABLE" in err:
                    wait = (attempt + 1) * 6
                    print(f"   Waiting {wait}s...")
                    time.sleep(wait)
                else:
                    break  # not a 503, try next model immediately
    raise Exception(f"All models failed. Last error: {last_error}")

# ── Known Tamil verse lookup table ───────────────────────────────────────────
# Key: first few unique Tamil words of the verse
# Value: (title, literary_era, verse_type)
KNOWN_VERSES = {
    "யாதும்": ("Purananuru 192 — Kaniyan Poonkundranar", "Sangam", "Puram (Heroic/Social)"),
    "யாயும்": ("Kuruntokai 40 — Sangam Agam Poetry", "Sangam", "Agam (Love)"),
    "அகர": ("Thirukkural — Kural 1 — Kadavul Vazhthu — Thiruvalluvar", "Didactic", "Venpa"),
    "அன்பும்": ("Thirukkural — Kural 45 — Thiruvalluvar", "Didactic", "Venpa"),
    "இன்னாசெய்தாரை": ("Thirukkural — Kural 314 — Thiruvalluvar", "Didactic", "Venpa"),
    "அச்சமில்லை": ("Acham Illai — Mahakavi Bharathiyar", "Modern", "Nationalism"),
    "என்னை": ("Thiruvasagam — Manikkavasagar", "Devotional", "Devotional"),
    "அவனரு": ("Thiruvasagam — Manikkavasagar", "Devotional", "Devotional"),
    "கண்ணன்": ("Bharathiyar — Kannan Pattu", "Modern", "Devotional lyric"),
}

def lookup_known_verse(text):
    """Check if text starts with a known verse pattern."""
    first_word = text.strip().split()[0] if text.strip() else ""
    return KNOWN_VERSES.get(first_word, None)



# ── Tanglish → Tamil ──────────────────────────────────────────────────────────
TANGLISH_MAP = {
    "aa": "ஆ", "ee": "ஈ", "oo": "ஊ", "ai": "ஐ", "au": "ஔ",
    "ng": "ங", "nj": "ஞ", "nd": "ண", "nn": "ன", "nt": "ந",
    "ny": "ந", "sh": "ஷ", "th": "த", "zh": "ழ", "ch": "ச",
    "a": "அ", "i": "இ", "u": "உ", "e": "எ", "o": "ஒ",
    "k": "க", "g": "க", "s": "ச", "j": "ஜ", "t": "ட",
    "d": "ட", "n": "ன", "p": "ப", "b": "ப", "m": "ம",
    "y": "ய", "r": "ர", "l": "ல", "v": "வ", "w": "வ",
    "h": "ஹ", "f": "ஃப",
}

def tanglish_to_tamil(text):
    words = re.split(r'(\s+|[,.!?;:()\[\]])', text)
    result = []
    for word in words:
        if not word or re.match(r'\s+|[,.!?;:()\[\]]', word):
            result.append(word)
            continue
        if re.search(r'[\u0B80-\u0BFF]', word):
            result.append(word)
            continue
        out = ""
        i = 0
        w = word.lower()
        while i < len(w):
            matched = False
            for combo in sorted(TANGLISH_MAP.keys(), key=len, reverse=True):
                if w[i:i+len(combo)] == combo:
                    out += TANGLISH_MAP[combo]
                    i += len(combo)
                    matched = True
                    break
            if not matched:
                out += w[i]
                i += 1
        result.append(out)
    return "".join(result)


def vaani_spellcheck(text, skip_words=None):
    """
    Vaani spellcheck with strict confidence filter.
    - skip_words: proper nouns / entity names — never corrected
    - Only correct if Vaani is CONFIDENT: flag=False AND top suggestion
      is clearly different AND the original word looks like a real mistake
      (i.e. original is NOT a valid Tamil word by Vaani's own check)
    - Never correct words longer than original (Vaani sometimes adds suffixes wrongly)
    """
    skip_words = skip_words or set()
    if not VAANI_AVAILABLE:
        return text, []
    tokens = re.split(r'(\s+|[,.!?;:()\[\]।\n])', text)
    corrected_tokens = []
    corrections = []
    for token in tokens:
        if not token or re.match(r'\s+|[,.!?;:()\[\]।\n]', token):
            corrected_tokens.append(token)
            continue
        if not re.search(r'[\u0B80-\u0BFF]', token):
            corrected_tokens.append(token)
            continue
        # Never correct entity names / proper nouns
        if token in skip_words:
            corrected_tokens.append(token)
            continue
        # Skip very short words (1-2 chars) — too risky
        if len(token) <= 2:
            corrected_tokens.append(token)
            continue
        # Skip words with வாழ் / நட / இரு roots — Vaani often wrong on these verb forms
        SKIP_ROOTS = ["வாழ", "நட", "இரு", "செய", "சொல", "கற", "படி", "பாடி"]
        if any(token.startswith(root) for root in SKIP_ROOTS):
            corrected_tokens.append(token)
            continue
        try:
            flag, suggestions = VaaniChecker.REST_interface(token, token)
            if (not flag
                and suggestions
                and suggestions[0] != token
                # Never accept a suggestion longer than original — Vaani adds wrong suffixes
                and len(suggestions[0]) <= len(token)
                # Must be meaningfully different (not just a diacritic change)
                and suggestions[0][:2] == token[:2]  # same root start
            ):
                corrections.append({"original": token, "corrected": suggestions[0]})
                corrected_tokens.append(suggestions[0])
            else:
                corrected_tokens.append(token)
        except Exception:
            corrected_tokens.append(token)
    return "".join(corrected_tokens), corrections


def detect_content_type_basic(text):
    """Fast line-count based detection as fallback."""
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    words = text.split()
    if len(lines) == 2:
        return "couplet"
    if len(lines) >= 3:
        return "verse"
    if len(words) > 25:
        return "paragraph"
    return "sentence"

def detect_content_type(text):
    """
    Smart detection using AI — works even if verse/kural is written in a single line.
    Falls back to line-count if AI call fails.
    """
    # If already multiline, use fast detection directly
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    if len(lines) >= 2:
        return detect_content_type_basic(text)

    # Single line — ask AI to classify it
    try:
        prompt = (
            "Classify this Tamil text into exactly one category. "
            "Reply with ONLY one word — sentence, paragraph, kural, or verse.\n\n"
            "Rules:\n"
            "- sentence: a normal Tamil sentence or news text\n"
            "- paragraph: long prose with multiple ideas (>25 words)\n"
            "- couplet: any 2-line Tamil verse written in one line (Thirukkural, Purananuru, Sangam couplet, Bible verse, etc.)\n"
            "- verse: a multi-line Tamil poem written in one line (Bharathiyar, Thevaram, Sangam poem, etc.)\n\n"
            "Text: " + text
        )
        result = generate(prompt).strip().lower()
        if result in ("sentence", "paragraph", "couplet", "verse"):
            return result
        # If AI returned something unexpected, fall back
        return detect_content_type_basic(text)
    except Exception:
        return detect_content_type_basic(text)


NER_PROMPT = """You are a highly accurate Tamil Named Entity Recognition (NER) engine and cultural scholar.

Your task: Read the Tamil text carefully and extract EVERY named entity with 100% accuracy.

ENTITY TYPES — choose the BEST fit:
- PERSON      : Real humans — poets, kings, saints, leaders, authors, reformers
                Examples: கம்பன், திருவள்ளுவர், பாரதியார், அம்பேத்கர், பெரியார்
- PLACE       : Real geographic locations — cities, countries, rivers, mountains, temples, regions, states
                Examples: சென்னை, இலங்கை, காவிரி, இமயமலை, திருப்பதி, தமிழ்நாடு
- ORGANIZATION: Institutions, universities, parties, companies, religious bodies
                Examples: அண்ணா பல்கலைக்கழகம், திமுக, இந்திய தேசிய காங்கிரஸ்
- MYTH        : Mythological/legendary beings — gods, goddesses, demons, epic heroes/villains
                Examples: இராவணன், அனுமன், முருகன், சீதை, கிருஷ்ணன், சிவன், விஷ்ணு
- LITERATURE  : Named literary works — books, epics, poems, scriptures, collections
                Examples: திருக்குறள், இராமாயணம், சிலப்பதிகாரம், தேவாரம், மணிமேகலை
- CULTURAL    : Art forms, music styles, dance forms, cultural practices, customs
                Examples: பரதநாட்டியம், கர்னாடக இசை, கரகாட்டம், தேர்த்திருவிழா
- FESTIVAL    : Named festivals, celebrations, religious events
                Examples: பொங்கல், தீபாவளி, தைப்பூசம், நவராத்திரி, ஆடி அமாவாசை
- FOOD        : Traditional Tamil dishes, foods, ingredients
                Examples: இட்லி, தோசை, பொங்கல் (dish), சாம்பார், கொழுக்கட்டை
- DYNASTY     : Named kingdoms, dynasties, ruling clans, empires
                Examples: சோழர், பாண்டியர், பல்லவர், சேரர், நாயக்கர், மராட்டியர்

CRITICAL RULES:
1. Extract the EXACT word/phrase as it appears in the text — do not modify spelling
2. If an entity appears multiple times, list it ONLY ONCE
3. Do NOT label common Tamil words as entities (e.g. தமிழ் alone is not an entity unless referring to a specific work/person)
4. Do NOT split compound entity names — keep them as one (e.g. "அண்ணா பல்கலைக்கழகம்" is ONE entity)
5. NEVER confuse MYTH (fictional/divine) with PERSON (real historical human)
6. LITERATURE = named works only. PERSON = the author. Both can exist for same sentence.
7. Explanations must be simple, accurate, 2-3 sentences for a 10-year-old diaspora Tamil student

Return ONLY this valid JSON — no markdown, no extra text, no preamble:
{
  "entities": [
    {
      "word": "exact Tamil word or phrase from text",
      "type": "PERSON|PLACE|ORGANIZATION|MYTH|LITERATURE|CULTURAL|FESTIVAL|FOOD|DYNASTY",
      "explanation_en": "2-3 sentence explanation in simple English",
      "explanation_ta": "2-3 sentence explanation in simple Tamil script"
    }
  ]
}

If no named entities found, return exactly: {"entities": []}"""


VERSE_PROMPT = """You are an expert Tamil language scholar helping diaspora Tamil students understand Tamil verses.

This is a multi-line Tamil verse. It could be from ANY of these traditions:
- Sangam Agam poetry (love/nature — Akananuru, Natrinai, Kuruntokai, Ainkurunuru, Kalittokai)
- Sangam Puram poetry (heroic/social — Purananuru, Pathirruppattu, Paripadal)
- Devotional poetry (Shaivite Thevaram, Thiruvasagam; Vaishnavite Divya Prabandham)
- Epic poetry (Silappatikaram, Manimekalai, Kamba Ramayanam)
- Didactic poetry (Naladiyar, Pazhamozhi, Thirukkural extended sections)
- Modern poetry (Bharathiyar, Bharathidasan, Subramania Bharati — nationalism/freedom/social reform)
- Free verse / Pudhukkavithai (modern experimental Tamil poetry)
- Biblical Tamil poetry (Psalms/Sangeetham, Prophetic verses)

Identify the tradition and return ONLY valid JSON:
{

  "literary_era": "Sangam / Devotional / Epic / Didactic / Modern / Biblical / Other",
  "verse_type": "Agam (love) / Puram (heroic) / Devotional / Epic / Didactic / Nationalism / Free verse / Other",
  "overall_meaning": "2-3 sentence summary of what the full verse means in simple English",
  "overall_meaning_ta": "2-3 sentence summary in simple Tamil",
  "lines": [
    {
      "line": "exact line from text",
      "transliteration": "pronunciation in English letters",
      "meaning_en": "clear English meaning of this line",
      "meaning_ta": "meaning in simple Tamil"
    }
  ],
  "cultural_context": "1-2 sentences about the literary tradition and historical background",
  "fun_fact": "one interesting fact about this verse, poet, or the tradition it belongs to"
}
Rules: Simple enough for a 10-year-old diaspora student. Return ONLY JSON, no markdown."""

KURAL_PROMPT = """You are an expert Tamil language scholar helping diaspora Tamil students understand Tamil literature.

This is a 2-line Tamil couplet. It could be from ANY of these works:
- Thirukkural (Venpa couplet by Thiruvalluvar — ethics, love, statecraft)
- Purananuru / Akananuru (Sangam Puram/Agam poetry)
- Natrinai / Kuruntokai (Sangam love poetry)
- Thevaram / Thiruvasagam (Shaivite devotional — Nayanars)
- Divya Prabandham (Vaishnavite devotional — Alvars)
- Silappatikaram / Manimekalai (Tamil epics)
- Naladiyar (Jain didactic poetry)
- Bible Tamil verses (Vachanam / Sangeetham / Theerkadharisanam)
- Bharathiyar / modern Tamil couplets
- OR any other Tamil literary work

WARNING: Tamil has thousands of classical verses. Most 2-line couplets are NOT Thirukkural.
Thirukkural = ONLY the 1330 kurals by Thiruvalluvar. Any doubt = NOT Thirukkural.

STRICT IDENTIFICATION — follow these rules exactly:

KNOWN VERSES — if input matches, use this identity:
- யாதும் ஊரே யாவரும் கேளிர் = Purananuru 192 by Kaniyan Poonkundranar (Sangam Puram). THIS IS NOT THIRUKKURAL.
- அகர முதல எழுத்தெல்லாம் ஆதி = Thirukkural Kural 1 by Thiruvalluvar
- யாயும் ஞாயும் யாரா கியரோ = Kuruntokai 40, Sangam Agam
- அச்சமில்லை அச்சமில்லை = Acham Illai by Bharathiyar

HOW TO IDENTIFY (check in order):
1. Match against known verses above first
2. Thirukkural uses strict Kural Venpa meter — 4+3 syllable feet per line, moral/ethical content by Thiruvalluvar only
3. Sangam style = nature imagery, love or heroic themes, ancient Tamil
4. Devotional = praises Shiva or Vishnu
5. Modern = freedom, social reform themes
6. If UNSURE — set title_guess to Unknown classical Tamil couplet. NEVER default to Thirukkural.

Return ONLY valid JSON:
{

  "literary_era": "Sangam / Didactic / Devotional / Epic / Modern / Biblical / Unknown",
  "verse_type": "Venpa / Asiriyappa / Kalippa / Vanchippa / Free verse / Prose verse / Other",
  "overall_meaning": "full meaning of both lines in simple English (2-3 sentences)",
  "overall_meaning_ta": "full meaning in simple Tamil (2-3 sentences)",
  "lines": [
    {
      "line": "exact first line",
      "transliteration": "pronunciation in English letters",
      "meaning_en": "meaning of this line in English",
      "meaning_ta": "meaning of this line in Tamil"
    },
    {
      "line": "exact second line",
      "transliteration": "pronunciation in English letters",
      "meaning_en": "meaning of this line in English",
      "meaning_ta": "meaning of this line in Tamil"
    }
  ],
  "moral": "the life lesson or message this couplet teaches in one sentence",
  "cultural_context": "1-2 sentences about the literary tradition this verse belongs to",
  "fun_fact": "one interesting fact about this verse, its author, or the work"
}
Rules: Simple enough for a 10-year-old diaspora student. Return ONLY JSON, no markdown."""


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    raw_text = data.get("text", "").strip()
    is_tanglish = data.get("is_tanglish", False)

    if not raw_text:
        return jsonify({"error": "No text provided"}), 400

    # Step 1: If Tanglish, let Gemini convert it properly (much better than manual map)
    if is_tanglish:
        tanglish_prompt = "Convert this Tanglish to proper Tamil script. Return ONLY Tamil script, nothing else: " + raw_text
        converted_text = generate(tanglish_prompt)
    else:
        converted_text = raw_text

    # Step 2: Detect content type
    content_type = detect_content_type(converted_text)

    # Step 3: Vaani spellcheck — only for sentence and paragraph
    if content_type in ("sentence", "paragraph"):
        # Quick NER pass to protect proper nouns from Vaani correction
        try:
            quick_ner = generate(
                "List ONLY the named entity words (persons, places, myths, organizations) "
                "from this Tamil text as a comma-separated list. No explanations, just the words:\n\n" + converted_text
            )
            protected = set(re.findall(r'[\u0B80-\u0BFF]+', quick_ner))
        except Exception:
            protected = set()
        spell_corrected_text, corrections = vaani_spellcheck(converted_text, skip_words=protected)
    else:
        # verse/kural/poem — no Vaani, no NER, just use text as-is
        spell_corrected_text, corrections = converted_text, []

    try:
        def clean_json(raw):
            raw = raw.strip()
            raw = re.sub(r'^```json\s*', '', raw)
            raw = re.sub(r'^```\s*', '', raw)
            raw = re.sub(r'\s*```$', '', raw)
            # Find JSON object if wrapped in extra text
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                raw = match.group(0)
            return raw.strip()

        meaning_result = None
        ner_result = {"entities": []}

        if content_type in ("sentence", "paragraph"):
            # NER only for sentence and paragraph
            ner_raw = clean_json(generate(f"{NER_PROMPT}\n\nTamil text to analyze:\n\n{spell_corrected_text}"))
            try:
                ner_result = json.loads(ner_raw)
            except json.JSONDecodeError:
                # Try to fix truncated JSON
                if not ner_raw.endswith("}"):
                    ner_raw += ']}'
                ner_result = json.loads(ner_raw)
            # Validate entity types — fix any wrong types
            valid_types = {"PERSON","PLACE","ORGANIZATION","MYTH","LITERATURE","CULTURAL","FESTIVAL","FOOD","DYNASTY"}

            # Common Tamil verbs/words that should NEVER be entities
            FALSE_POSITIVES = {
                "என்று","என்னும்","என்ற","என்பது","என்பதால்","என்றால்",
                "சொல்லபடுகிறது","சொன்னார்","சொல்கிறார்","சொன்னான்",
                "வாழ்ந்தார்","வாழ்ந்தான்","வாழ்கிறார்","வாழனது","வாலனது",
                "கற்பிக்கிறது","கற்றார்","படித்தார்","எழுதினார்","எழுதினான்",
                "ஆட்சி","செய்தான்","செய்தார்","செய்கிறார்","நடந்தது",
                "இருந்தான்","இருந்தார்","இருக்கிறார்","இருக்கிறது",
                "போனான்","போனார்","வந்தான்","வந்தார்","கொண்டனர்",
                "பாடல்கள்","பாடினான்","பாடினார்","கொண்டாடினார்",
                "தமிழ்","தமிழர்","மக்கள்","நாடு","ஊர்","நகரம்",
            }

            filtered_entities = []
            for ent in ner_result.get("entities", []):
                if ent.get("type") not in valid_types:
                    ent["type"] = "CULTURAL"
                # Skip if word is a known false positive
                if ent.get("word","") in FALSE_POSITIVES:
                    continue
                # Skip if word is very short (1-2 chars)
                if len(ent.get("word","")) <= 2:
                    continue
                filtered_entities.append(ent)
            ner_result["entities"] = filtered_entities

        elif content_type == "couplet":
            # Check known verse lookup first before calling AI
            known = lookup_known_verse(spell_corrected_text)
            m_raw = clean_json(generate(f"{KURAL_PROMPT}\n\nTamil couplet:\n\n{spell_corrected_text}"))
            meaning_result = json.loads(m_raw)
            meaning_result["mode"] = "couplet"
            # Override AI title/era/type if we know the verse for sure
            if known:
                meaning_result["title_guess"] = known[0]
                meaning_result["literary_era"] = known[1]
                meaning_result["verse_type"] = known[2]

        elif content_type == "verse":
            # Verse: meaning only, no NER
            m_raw = clean_json(generate(f"{VERSE_PROMPT}\n\nVerse:\n\n{spell_corrected_text}"))
            meaning_result = json.loads(m_raw)
            meaning_result["mode"] = "verse"

        return jsonify({
            "original_text": raw_text,
            "converted_text": converted_text,
            "corrected_text": spell_corrected_text,
            "corrections": corrections,
            "vaani_active": VAANI_AVAILABLE and content_type in ("sentence", "paragraph"),
            "content_type": content_type,
            "entities": ner_result.get("entities", []),
            "meaning": meaning_result,
            "was_tanglish": is_tanglish
        })
    except json.JSONDecodeError as e:
        return jsonify({"error": f"JSON parse error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/explain", methods=["POST"])
def explain():
    data = request.get_json()
    word = data.get("word", "")
    entity_type = data.get("type", "")
    context = data.get("context", "")
    try:
        prompt = (
            f"Give a detailed, student-friendly explanation of the Tamil entity '{word}' "
            f"(type: {entity_type}) in context: '{context}'. "
            f"Include historical/cultural significance and interesting stories. "
            f"English only, 3-4 paragraphs, for a diaspora Tamil teenager."
        )
        explanation = generate(prompt)
        return jsonify({"explanation": explanation})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("\n⚠️  WARNING: GEMINI_API_KEY not set!")
        print("   Set it with: export GEMINI_API_KEY='your-key-here'\n")
    else:
        print(f"\n✅ Gemini API key loaded ({key[:8]}...)")
    print(f"📋 {len(MODELS)} models in fallback list")
    print("🚀 Tamil Content X-Ray starting on http://localhost:5000\n")
    app.run(debug=True, port=5000)
