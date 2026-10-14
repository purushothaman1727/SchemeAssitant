import { createContext, ReactNode, useContext, useEffect, useState } from "react";

export type Lang = "en" | "ta";

// Tamil strings were drafted by the developer and need review by a fluent speaker.
const dict = {
  en: {
    appName: "Scheme Assistant",
    independent:
      "Independent assistance tool. Not an official government website. Results are preliminary and must be confirmed with the issuing authority.",
    navHome: "Home", navFind: "Find schemes", navSchemes: "Browse schemes", navChat: "Chat", navPrivacy: "Privacy",
    homeTitle: "Find government schemes that may fit your situation",
    homeLead: "Answer a few questions. We check them against published scheme rules and show the official sources.",
    start: "Start",
    stepApplicant: "Applicant", stepHousehold: "Household", stepDisability: "Disability", stepDetails: "More details", stepReview: "Review",
    back: "Back", next: "Next", submit: "See recommendations", required: "This field is required",
    applyingFor: "Who is this for?", forSelf: "Myself", forChild: "My child (I am the parent or legal guardian)",
    age: "Age of the applicant (years)", state: "State / Union Territory", district: "District",
    income: "Annual family income (₹)", incomeHint: "Approximate figure is fine. Leave blank if unknown.",
    occupation: "Occupation", education: "Education level", isStudent: "Currently a student?",
    disabilityQ: "Does the applicant have a disability?",
    disYes: "Yes, the applicant is a person with a disability.", disNo: "No.", disPreferNot: "Prefer not to say.",
    disType: "Type of disability", certStatus: "Disability certificate / UDID status",
    pct: "Disability percentage (if on certificate)", unknown: "Not sure / not applicable", yes: "Yes", no: "No",
    detailsIntro: "These questions are optional. Answering them lets us check more schemes; leave any blank if unsure.",
    qGuardian: "Does the parent or guardian have a disability?",
    qBpl: "Is the household below the poverty line (BPL)?",
    qWidow: "Is the applicant a widow?",
    qLand: "Cultivable land held by the family (hectares)",
    qNotified: "Is the course at an institute notified under the scholarship scheme?",
    qRegistered: "Registered as unemployed with the employment exchange for over a year?",
    qHighSupport: "Certified as having high support need?",
    qListed: "Does the person have Parkinson's disease, spinal cord injury, multiple sclerosis, muscular dystrophy, or is leprosy-affected?",
    consent: "I agree that my answers may be processed to produce recommendations. They stay in this browser session and are not stored on the server.",
    reviewNote: "Nothing here is an application. We do not collect names, phone numbers, Aadhaar or documents.",
    // results
    resultsTitle: "Your scheme results", resultsLead: "These are preliminary results based on the details you gave.",
    loading: "Checking schemes…", retry: "Try again", editAnswers: "Edit my answers",
    noProfile: "Please answer the questions first so we can check schemes.",
    showMore: "Show schemes that do not match", hideMore: "Hide schemes that do not match",
    noResults: "No schemes matched the details given. Try editing your answers, or browse all schemes.",
    sPotentially_eligible: "Potentially eligible", sMore_information_required: "More information required",
    sDoes_not_match: "Does not match known criteria", sInformation_unverified: "Eligibility information unverified",
    whyRelevant: "Why it may be relevant", whyStatus: "Why this status", missingInfo: "Information needed",
    benefits: "Benefits", documents: "Documents", steps: "How to apply", officialSource: "Official source",
    applyLink: "Official application link", lastVerified: "Last verified", limitations: "Important limitations",
    askChat: "Ask the assistant", details: "Scheme details", central: "Central Government", tamilNadu: "Tamil Nadu Government",
    noneRecorded: "None recorded in our verified data.",
    // schemes
    schemesTitle: "Browse schemes", search: "Search", allJurisdictions: "All governments", allCategories: "All categories",
    allAudiences: "All beneficiaries", category: "Category", beneficiary: "Beneficiary", prev: "Previous", pageOf: "Page",
    verification: "Verification", rulesTitle: "Eligibility rules recorded", sourcesTitle: "Sources",
    verifiedRule: "verified", unverifiedRule: "not verified", mandatory: "mandatory", notesTitle: "Verification notes",
    // chat
    chatTitle: "Ask about schemes", chatPlaceholder: "Type your question…", send: "Send", thinking: "Thinking…",
    chatIntro: "Ask about eligibility, benefits, documents or how to apply. Answers use the verified scheme records and official documents, with sources.",
    usingProfile: "Use my answers to personalise replies", saveChat: "Save this conversation for 30 days (optional)",
    deleteChat: "Delete saved conversation", sources: "Sources", moreInfoNeeded: "I may need:",
    answerLang: "Answer language", langAuto: "Same as my question",
    notBuilt: "This page is connected in a later build phase.",
    heroEyebrow: "Independent guide to Central and Tamil Nadu schemes",
    heroSub: "Free to use. No sign-up. Skip any question you prefer not to answer.",
    howTitle: "How it works",
    how1t: "Tell us a little", how1b: "A short form. Skip anything you prefer not to share.",
    how2t: "We check published rules", how2b: "Each scheme is matched against its verified criteria, not guessed by AI.",
    how3t: "See sources and next steps", how3b: "Every result links to the official page, with documents and how to apply.",
    trust1t: "Official sources, with dates", trust1b: "Every scheme shows where it came from and when it was last checked.",
    trust2t: "Private by default", trust2b: "Your answers stay in your browser tab. We never ask for Aadhaar or documents.",
    trust3t: "English and Tamil", trust3b: "Use the whole app and the assistant in either language.",
    sugg1: "What documents do I need for UDID?", sugg2: "How much is the unemployment allowance?",
    sugg3: "Which scholarships can I explore?", suggTitle: "Try asking",
    footerNote: "An independent assistance tool. Scheme data is checked against official sources on the dates shown on each scheme.",
    filterAll: "All", stepOf: "Step", of: "of", assistant: "Assistant", you: "You",
    menu: "Menu", skipToContent: "Skip to content", resultsCount: "schemes shown",
  },
  ta: {
    appName: "திட்ட உதவியாளர்",
    independent:
      "இது ஒரு சுதந்திரமான உதவிக் கருவி; அரசின் அதிகாரப்பூர்வ இணையதளம் அல்ல. இவை முதற்கட்ட மதிப்பீடுகள் மட்டுமே; தொடர்புடைய அதிகாரியிடம் உறுதிசெய்து கொள்ளவும்.",
    navHome: "முகப்பு", navFind: "திட்டங்களைக் கண்டறிக", navSchemes: "திட்டங்கள்", navChat: "அரட்டை", navPrivacy: "தனியுரிமை",
    homeTitle: "உங்கள் சூழலுக்குப் பொருந்தக்கூடிய அரசுத் திட்டங்களைக் கண்டறியுங்கள்",
    homeLead: "சில கேள்விகளுக்குப் பதிலளியுங்கள். வெளியிடப்பட்ட திட்ட விதிகளுடன் சரிபார்த்து, அதிகாரப்பூர்வ ஆதாரங்களைக் காட்டுவோம்.",
    start: "தொடங்கு",
    stepApplicant: "விண்ணப்பதாரர்", stepHousehold: "குடும்பம்", stepDisability: "மாற்றுத்திறன்", stepDetails: "கூடுதல் விவரம்", stepReview: "சரிபார்",
    back: "பின்", next: "அடுத்து", submit: "பரிந்துரைகளைக் காண்க", required: "இந்தப் புலம் அவசியம்",
    applyingFor: "இது யாருக்காக?", forSelf: "எனக்காக", forChild: "என் குழந்தைக்காக (நான் பெற்றோர்/சட்டப்பூர்வ பாதுகாவலர்)",
    age: "விண்ணப்பதாரரின் வயது (ஆண்டுகள்)", state: "மாநிலம் / யூனியன் பிரதேசம்", district: "மாவட்டம்",
    income: "ஆண்டு குடும்ப வருமானம் (₹)", incomeHint: "தோராயமான தொகை போதும். தெரியாவிட்டால் காலியாக விடவும்.",
    occupation: "தொழில்", education: "கல்வி நிலை", isStudent: "தற்போது மாணவரா?",
    disabilityQ: "விண்ணப்பதாரருக்கு மாற்றுத்திறன் உள்ளதா?",
    disYes: "ஆம், விண்ணப்பதாரர் மாற்றுத்திறனாளி.", disNo: "இல்லை.", disPreferNot: "சொல்ல விரும்பவில்லை.",
    disType: "மாற்றுத்திறன் வகை", certStatus: "மாற்றுத்திறன் சான்றிதழ் / UDID நிலை",
    pct: "மாற்றுத்திறன் சதவீதம் (சான்றிதழில் இருந்தால்)", unknown: "தெரியவில்லை / பொருந்தாது", yes: "ஆம்", no: "இல்லை",
    detailsIntro: "இந்தக் கேள்விகள் விருப்பத்திற்குரியவை. பதிலளித்தால் கூடுதல் திட்டங்களைச் சரிபார்க்க முடியும்; உறுதியில்லாதவற்றை காலியாக விடலாம்.",
    qGuardian: "பெற்றோர்/பாதுகாவலருக்கு மாற்றுத்திறன் உள்ளதா?",
    qBpl: "குடும்பம் வறுமைக் கோட்டிற்குக் கீழ் (BPL) உள்ளதா?",
    qWidow: "விண்ணப்பதாரர் விதவையா?",
    qLand: "குடும்பத்திடம் உள்ள பயிரிடும் நிலம் (ஹெக்டேர்)",
    qNotified: "இந்தப் படிப்பு உதவித்தொகைத் திட்டத்தில் அறிவிக்கப்பட்ட நிறுவனத்தில் உள்ளதா?",
    qRegistered: "வேலைவாய்ப்பு அலுவலகத்தில் ஒரு ஆண்டுக்கு மேல் வேலையற்றவராகப் பதிவு செய்துள்ளீர்களா?",
    qHighSupport: "உயர் ஆதரவு தேவை உள்ளவர் என சான்றளிக்கப்பட்டுள்ளதா?",
    qListed: "பார்கின்சன் நோய், முதுகுத்தண்டு காயம், பலமுனை நரம்பு தடிப்பு, தசை சிதைவு நோய் உள்ளதா, அல்லது தொழுநோயால் பாதிக்கப்பட்டவரா?",
    consent: "பரிந்துரைகளை உருவாக்க என் பதில்களைச் செயலாக்க ஒப்புக்கொள்கிறேன். அவை இந்த உலாவி அமர்வில் மட்டுமே இருக்கும்; சேவையகத்தில் சேமிக்கப்படாது.",
    reviewNote: "இங்கே எதுவும் விண்ணப்பம் அல்ல. பெயர், தொலைபேசி எண், ஆதார் அல்லது ஆவணங்களை நாங்கள் சேகரிக்கவில்லை.",
    resultsTitle: "உங்கள் திட்ட முடிவுகள்", resultsLead: "நீங்கள் அளித்த விவரங்களின் அடிப்படையிலான முதற்கட்ட முடிவுகள் இவை.",
    loading: "திட்டங்களைச் சரிபார்க்கிறோம்…", retry: "மீண்டும் முயற்சிக்கவும்", editAnswers: "என் பதில்களைத் திருத்து",
    noProfile: "திட்டங்களைச் சரிபார்க்க முதலில் கேள்விகளுக்குப் பதிலளிக்கவும்.",
    showMore: "பொருந்தாத திட்டங்களையும் காட்டு", hideMore: "பொருந்தாத திட்டங்களை மறை",
    noResults: "கொடுத்த விவரங்களுக்கு எந்தத் திட்டமும் பொருந்தவில்லை. பதில்களைத் திருத்தவும் அல்லது அனைத்துத் திட்டங்களையும் பார்க்கவும்.",
    sPotentially_eligible: "தகுதி பெற வாய்ப்புள்ளது", sMore_information_required: "மேலும் தகவல் தேவை",
    sDoes_not_match: "அறியப்பட்ட நிபந்தனைகளுடன் பொருந்தவில்லை", sInformation_unverified: "தகுதி விவரங்கள் சரிபார்க்கப்படவில்லை",
    whyRelevant: "ஏன் பொருத்தமாக இருக்கலாம்", whyStatus: "இந்த நிலைக்கான காரணம்", missingInfo: "தேவையான தகவல்",
    benefits: "பலன்கள்", documents: "ஆவணங்கள்", steps: "விண்ணப்பிக்கும் முறை", officialSource: "அதிகாரப்பூர்வ ஆதாரம்",
    applyLink: "அதிகாரப்பூர்வ விண்ணப்ப இணைப்பு", lastVerified: "கடைசியாகச் சரிபார்த்தது", limitations: "முக்கிய வரம்புகள்",
    askChat: "உதவியாளரிடம் கேளுங்கள்", details: "திட்ட விவரங்கள்", central: "மத்திய அரசு", tamilNadu: "தமிழ்நாடு அரசு",
    noneRecorded: "எங்கள் சரிபார்க்கப்பட்ட தரவில் பதிவு இல்லை.",
    schemesTitle: "திட்டங்களைப் பார்க்க", search: "தேடு", allJurisdictions: "அனைத்து அரசுகள்", allCategories: "அனைத்து வகைகள்",
    allAudiences: "அனைத்துப் பயனாளிகள்", category: "வகை", beneficiary: "பயனாளி", prev: "முந்தைய", pageOf: "பக்கம்",
    verification: "சரிபார்ப்பு", rulesTitle: "பதிவு செய்யப்பட்ட தகுதி விதிகள்", sourcesTitle: "ஆதாரங்கள்",
    verifiedRule: "சரிபார்க்கப்பட்டது", unverifiedRule: "சரிபார்க்கப்படவில்லை", mandatory: "கட்டாயம்", notesTitle: "சரிபார்ப்புக் குறிப்புகள்",
    chatTitle: "திட்டங்கள் பற்றிக் கேளுங்கள்", chatPlaceholder: "உங்கள் கேள்வியை எழுதுங்கள்…", send: "அனுப்பு", thinking: "யோசிக்கிறேன்…",
    chatIntro: "தகுதி, பலன்கள், ஆவணங்கள் அல்லது விண்ணப்பிக்கும் முறை பற்றிக் கேளுங்கள். பதில்கள் சரிபார்க்கப்பட்ட பதிவுகள் மற்றும் அதிகாரப்பூர்வ ஆவணங்களை ஆதாரங்களுடன் பயன்படுத்துகின்றன.",
    usingProfile: "பதில்களைத் தனிப்பயனாக்க என் விவரங்களைப் பயன்படுத்து", saveChat: "இந்த உரையாடலை 30 நாட்கள் சேமி (விருப்பம்)",
    deleteChat: "சேமித்த உரையாடலை நீக்கு", sources: "ஆதாரங்கள்", moreInfoNeeded: "எனக்குத் தேவைப்படலாம்:",
    answerLang: "பதில் மொழி", langAuto: "என் கேள்வியின் மொழி",
    notBuilt: "இந்தப் பக்கம் அடுத்த கட்டத்தில் இணைக்கப்படும்.",
    heroEyebrow: "மத்திய மற்றும் தமிழ்நாடு அரசுத் திட்டங்களுக்கான சுதந்திரமான வழிகாட்டி",
    heroSub: "இலவசம். பதிவு தேவையில்லை. பதிலளிக்க விரும்பாத கேள்வியைத் தவிர்க்கலாம்.",
    howTitle: "இது எவ்வாறு செயல்படுகிறது",
    how1t: "சில விவரங்களைச் சொல்லுங்கள்", how1b: "சிறிய படிவம். பகிர விரும்பாததைத் தவிர்க்கலாம்.",
    how2t: "வெளியிடப்பட்ட விதிகளைச் சரிபார்க்கிறோம்", how2b: "ஒவ்வொரு திட்டமும் சரிபார்க்கப்பட்ட நிபந்தனைகளுடன் ஒப்பிடப்படுகிறது; AI ஊகிப்பதில்லை.",
    how3t: "ஆதாரங்களையும் அடுத்த படிகளையும் காணுங்கள்", how3b: "ஒவ்வொரு முடிவும் அதிகாரப்பூர்வ பக்கம், ஆவணங்கள், விண்ணப்ப முறையுடன் இணைக்கப்பட்டுள்ளது.",
    trust1t: "தேதியுடன் கூடிய அதிகாரப்பூர்வ ஆதாரங்கள்", trust1b: "ஒவ்வொரு திட்டமும் எங்கிருந்து வந்தது, எப்போது சரிபார்க்கப்பட்டது என்பதைக் காட்டுகிறது.",
    trust2t: "இயல்பாகவே தனிப்பட்டது", trust2b: "உங்கள் பதில்கள் உங்கள் உலாவி தாவலிலேயே இருக்கும். ஆதார் அல்லது ஆவணங்களை நாங்கள் கேட்பதில்லை.",
    trust3t: "ஆங்கிலம் மற்றும் தமிழ்", trust3b: "முழு செயலியையும் உதவியாளரையும் இரு மொழிகளிலும் பயன்படுத்தலாம்.",
    sugg1: "UDID அட்டைக்கு என்ன ஆவணங்கள் தேவை?", sugg2: "வேலையில்லா உதவித்தொகை எவ்வளவு?",
    sugg3: "நான் எந்த உதவித்தொகைகளைப் பார்க்கலாம்?", suggTitle: "இவற்றைக் கேட்டுப் பாருங்கள்",
    footerNote: "இது ஒரு சுதந்திரமான உதவிக் கருவி. ஒவ்வொரு திட்டத்திலும் காட்டப்பட்டுள்ள தேதிகளில் தரவு அதிகாரப்பூர்வ ஆதாரங்களுடன் சரிபார்க்கப்பட்டது.",
    filterAll: "அனைத்தும்", stepOf: "படி", of: "/", assistant: "உதவியாளர்", you: "நீங்கள்",
    menu: "பட்டி", skipToContent: "உள்ளடக்கத்திற்குச் செல்", resultsCount: "திட்டங்கள் காட்டப்படுகின்றன",
  },
} as const;

export type TKey = keyof (typeof dict)["en"];

interface I18nCtx {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (k: TKey) => string;
}

const Ctx = createContext<I18nCtx | null>(null);

function loadLang(): Lang {
  try {
    return localStorage.getItem("lang") === "ta" ? "ta" : "en";
  } catch {
    return "en";
  }
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>(loadLang);
  useEffect(() => {
    document.documentElement.lang = lang;
    try {
      localStorage.setItem("lang", lang);
    } catch {
      /* storage unavailable */
    }
  }, [lang]);
  const t = (k: TKey) => dict[lang][k];
  return <Ctx.Provider value={{ lang, setLang, t }}>{children}</Ctx.Provider>;
}

export function useI18n(): I18nCtx {
  const c = useContext(Ctx);
  if (!c) throw new Error("useI18n outside provider");
  return c;
}
