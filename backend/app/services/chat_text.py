"""Static, human-reviewable strings and scheme-name matching for the chatbot.

Tamil strings are provided for the deterministic (non-LLM) paths; they should be reviewed by a
fluent speaker before public release.
"""
import re

SCHEME_ALIASES: dict[str, list[str]] = {
    "pre-matric-swd": ["pre-matric", "pre matric", "prematric", "class 9", "class ix",
                       "முன் மெட்ரிக்", "முந்தைய மெட்ரிக்", "மெட்ரிக்குக்கு முந்தைய"],
    "post-matric-swd": ["post-matric", "post matric", "postmatric",
                        "பிந்தைய மெட்ரிக்", "மெட்ரிக்குக்குப் பிந்தைய", "மெட்ரிக் பிந்தைய"],
    "top-class-swd": ["top class", "top-class", "டாப் கிளாஸ்", "உயர்தரக் கல்வி"],
    "aicte-saksham": ["saksham", "aicte", "சக்ஷம்", "சக்சம்"],
    "free-coaching-swd": ["free coaching", "coaching", "இலவசப் பயிற்சி"],
    "adip": ["adip", "aids and appliances", "assistive device", "appliance"],
    "ddrs": ["ddrs", "deendayal"],
    "udid": ["udid", "unique disability", "disability card", "swavlamban", "யுடிஐடி", "தனித்துவ மாற்றுத்திறனாளி"],
    "sipda": ["sipda"],
    "national-fund-pwd": ["national fund"],
    "ignd-ps": ["ignd", "disability pension", "indira gandhi national disability", "மாற்றுத்திறனாளி ஓய்வூதியம்"],
    "ignoa-ps": ["ignoa", "old age pension", "முதியோர் ஓய்வூதியம்", "முதியோர் உதவித்தொகை"],
    "ignw-ps": ["ignw", "widow pension", "விதவை ஓய்வூதியம்", "விதவை உதவித்தொகை"],
    "pm-kmy": ["maandhan", "maan dhan", "kisan pension", "pm-kmy", "kmy", "மான்தன்", "விவசாயி ஓய்வூதியம்"],
    "pm-jay": ["ayushman", "pm-jay", "pmjay", "jan arogya", "vay vandana", "ஆயுஷ்மான்"],
    "tn-ward-scholarship-welfare-board": ["son and daughter", "children of differently abled", "welfare board",
                                          "ward", "மகன் மற்றும் மகள்", "நல வாரியம்"],
    "tn-unemployment-allowance": ["unemployment allowance", "unemployment", "வேலையில்லா", "வேலையற்றோர்"],
    "tn-high-support-need-assistance": ["high support", "personal assistance", "care taker", "caretaker",
                                        "உயர் ஆதரவு", "அதிக ஆதரவு"],
    "tn-travel-concession": ["travel concession", "bus pass", "bus", "travel", "பேருந்து", "பயணச் சலுகை",
                             "இலவசப் பயணம்", "பயண அட்டை"],
    "tn-maintenance-allowance": ["maintenance allowance", "maintenance", "பராமரிப்பு உதவித்தொகை"],
}

FIELD_QUESTIONS: dict[str, dict[str, str]] = {
    "age": {"en": "What is the applicant's age?", "ta": "விண்ணப்பதாரரின் வயது என்ன?"},
    "state": {"en": "Which state does the applicant live in?", "ta": "விண்ணப்பதாரர் எந்த மாநிலத்தில் வசிக்கிறார்?"},
    "annual_family_income": {"en": "What is the approximate annual family income?", "ta": "ஆண்டு குடும்ப வருமானம் தோராயமாக எவ்வளவு?"},
    "education_level": {"en": "What is the current education level / class?", "ta": "தற்போதைய கல்வி நிலை / வகுப்பு என்ன?"},
    "disability_status": {"en": "Does the applicant have a disability? (You may choose not to say.)", "ta": "விண்ணப்பதாரருக்கு மாற்றுத்திறன் உள்ளதா? (சொல்ல விரும்பாவிட்டால் தவிர்க்கலாம்.)"},
    "disability_percentage": {"en": "What disability percentage is on the certificate?", "ta": "சான்றிதழில் உள்ள மாற்றுத்திறன் சதவீதம் என்ன?"},
    "studying_in_notified_institute": {"en": "Is the course at an institute notified under the scheme?", "ta": "இந்தப் படிப்பு திட்டத்தில் அறிவிக்கப்பட்ட நிறுவனத்தில் உள்ளதா?"},
    "guardian_has_disability": {"en": "Does the parent/guardian have a disability?", "ta": "பெற்றோர்/பாதுகாவலருக்கு மாற்றுத்திறன் உள்ளதா?"},
    "registered_unemployed_over_1_year": {"en": "Have you been registered as unemployed with the employment exchange for over a year?", "ta": "வேலைவாய்ப்பு அலுவலகத்தில் ஒரு ஆண்டுக்கு மேல் வேலையற்றவராக பதிவு செய்துள்ளீர்களா?"},
    "high_support_need_certified": {"en": "Is the person certified as having high support need?", "ta": "உயர் ஆதரவு தேவை உள்ளவர் என சான்றளிக்கப்பட்டுள்ளதா?"},
    "is_bpl": {"en": "Is the household below the poverty line (BPL)?", "ta": "குடும்பம் வறுமைக் கோட்டிற்குக் கீழ் (BPL) உள்ளதா?"},
    "is_widow": {"en": "Is the applicant a widow?", "ta": "விண்ணப்பதாரர் விதவையா?"},
    "land_holding_hectares": {"en": "How many hectares of cultivable land does the family hold?", "ta": "குடும்பத்திடம் எத்தனை ஹெக்டேர் பயிரிடும் நிலம் உள்ளது?"},
}

MSG = {
    "no_evidence": {
        "en": "I could not find official information for that in the documents I have, so I won't guess. "
              "Please check the official source for the scheme or ask a District Welfare Office.",
        "ta": "என்னிடம் உள்ள ஆவணங்களில் இதற்கான அதிகாரப்பூர்வ தகவல் கிடைக்கவில்லை, எனவே ஊகிக்க மாட்டேன். "
              "திட்டத்தின் அதிகாரப்பூர்வ இணையதளத்தை அல்லது மாவட்ட நலத்துறை அலுவலகத்தை அணுகவும்.",
    },
    "cannot_apply": {
        "en": "I can't submit applications or access any government system. I can only explain schemes. "
              "To apply, use the official application link shown for the scheme.",
        "ta": "என்னால் விண்ணப்பங்களைச் சமர்ப்பிக்கவோ அரசு அமைப்புகளை அணுகவோ முடியாது; திட்டங்களை மட்டுமே விளக்க முடியும். "
              "விண்ணப்பிக்க, திட்டத்திற்கான அதிகாரப்பூர்வ விண்ணப்ப இணைப்பைப் பயன்படுத்தவும்.",
    },
    "need_info": {
        "en": "To check this I need a little more information:",
        "ta": "இதைச் சரிபார்க்க எனக்கு மேலும் சில தகவல்கள் தேவை:",
    },
    "llm_down": {
        "en": "The AI assistant is not available right now, so here is what the verified records say:",
        "ta": "AI உதவியாளர் தற்போது கிடைக்கவில்லை; சரிபார்க்கப்பட்ட பதிவுகள் கூறுவது:",
    },
    "unvalidated": {
        "en": "I could not confirm every detail of a generated answer against the sources, so here is what the verified records say:",
        "ta": "உருவாக்கப்பட்ட பதிலின் அனைத்து விவரங்களையும் ஆதாரங்களுடன் உறுதிப்படுத்த முடியவில்லை; சரிபார்க்கப்பட்ட பதிவுகள் கூறுவது:",
    },
    "disclaimer": {
        "en": "This is general information and a preliminary check, not an official decision. Confirm with the official source.",
        "ta": "இது பொதுவான தகவல் மற்றும் முதற்கட்ட சரிபார்ப்பு மட்டுமே; அதிகாரப்பூர்வ முடிவு அல்ல. அதிகாரப்பூர்வ ஆதாரத்தில் உறுதிசெய்யவும்.",
    },
    "status": {
        "potentially_eligible": {"en": "Potentially eligible (on the verified criteria checked)", "ta": "தகுதி பெற வாய்ப்புள்ளது (சரிபார்க்கப்பட்ட நிபந்தனைகளின்படி)"},
        "more_information_required": {"en": "More information required", "ta": "மேலும் தகவல் தேவை"},
        "does_not_match": {"en": "Does not match known criteria", "ta": "அறியப்பட்ட நிபந்தனைகளுடன் பொருந்தவில்லை"},
        "information_unverified": {"en": "Eligibility information unverified", "ta": "தகுதி விவரங்கள் சரிபார்க்கப்படவில்லை"},
    },
}

_TAMIL = re.compile(r"[஀-௿]")
_APPLY_FOR_ME = re.compile(
    r"(apply|submit|register|file|enrol|enroll)\b.{0,25}\b(for me|on my behalf|it for me)|"
    r"\b(submit|file) (my|the) (application|form)|"
    r"(எனக்காக|என் சார்பாக).{0,20}(விண்ணப்பி|சமர்ப்பி)", re.IGNORECASE)
_ELIGIBILITY_Q = re.compile(
    r"(eligib|qualif|can i|am i|suitable|which schemes|what schemes|may be available|"
    r"தகுதி|பொருத்த|எந்த திட்ட)", re.IGNORECASE)


def detect_language(text: str) -> str:
    return "ta" if _TAMIL.search(text) else "en"


def is_apply_for_me(text: str) -> bool:
    return bool(_APPLY_FOR_ME.search(text))


def is_eligibility_question(text: str) -> bool:
    return bool(_ELIGIBILITY_Q.search(text))


def match_schemes(text: str) -> list[str]:
    low = text.lower()
    hits = []
    for sid, aliases in SCHEME_ALIASES.items():
        if any(a in low for a in aliases):
            hits.append(sid)
    # a specific name beats generic words such as "bus" / "coaching" / "ward"
    return hits


LABELS = {
    "benefits": {"en": "Benefits", "ta": "பலன்கள்"},
    "documents": {"en": "Documents", "ta": "ஆவணங்கள்"},
    "how": {"en": "How to apply", "ta": "விண்ணப்பிக்கும் முறை"},
    "source": {"en": "Official source", "ta": "அதிகாரப்பூர்வ ஆதாரம்"},
    "note": {"en": "Note", "ta": "குறிப்பு"},
}

# Fixed prefixes/sentences produced by the eligibility engine, shown in Tamil on the fallback path.
REASON_PREFIXES = {
    "Needed to check:": "சரிபார்க்கத் தேவை:",
    "Meets:": "பொருந்துவது:",
    "Does not meet:": "பொருந்தாதது:",
    "Note:": "குறிப்பு:",
}
REASON_SENTENCES = {
    "Based on the verified criteria checked here. Official verification and additional checks "
    "(documents, slots, application window) may still apply.":
        "இங்கு சரிபார்க்கப்பட்ட நிபந்தனைகளின் அடிப்படையிலானது. அதிகாரப்பூர்வ சரிபார்ப்பும் கூடுதல் "
        "சோதனைகளும் (ஆவணங்கள், இடங்கள், விண்ணப்பக் காலம்) இன்னும் பொருந்தக்கூடும்.",
    "Reliable current eligibility rules for this scheme could not be verified, so no eligibility "
    "assessment is made.":
        "இந்தத் திட்டத்தின் நம்பகமான தற்போதைய தகுதி விதிகளைச் சரிபார்க்க முடியவில்லை; எனவே தகுதி மதிப்பீடு செய்யப்படவில்லை.",
}


def label(key: str, lang: str) -> str:
    return LABELS[key][lang]


def localize_reason(text: str, lang: str) -> str:
    if lang != "ta":
        return text
    if text in REASON_SENTENCES:
        return REASON_SENTENCES[text]
    for en, ta in REASON_PREFIXES.items():
        if text.startswith(en):
            return ta + text[len(en):]
    return text


def t(key: str, lang: str) -> str:
    return MSG[key][lang]
