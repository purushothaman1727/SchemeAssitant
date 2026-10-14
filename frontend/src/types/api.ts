export type EligibilityStatus =
  | "potentially_eligible"
  | "more_information_required"
  | "does_not_match"
  | "information_unverified";

export interface ProfilePayload {
  applying_for: "self" | "child";
  age: number | null;
  state: string | null;
  district: string | null;
  annual_family_income: number | null;
  occupation: string | null;
  education_level: string | null;
  is_student: "yes" | "no" | "unknown";
  disability_status: "yes" | "no" | "prefer_not_to_say";
  disability_type: string | null;
  certificate_status: string | null;
  disability_percentage: number | null;
  guardian_has_disability: boolean | null;
  is_bpl: boolean | null;
  is_widow: boolean | null;
  land_holding_hectares: number | null;
  studying_in_notified_institute: boolean | null;
  registered_unemployed_over_1_year: boolean | null;
  high_support_need_certified: boolean | null;
  has_listed_chronic_condition: boolean | null;
}

export interface RecommendationCard {
  scheme_id: string;
  name: string;
  name_ta: string | null;
  jurisdiction: string;
  jurisdiction_label: string;
  category: string;
  status: EligibilityStatus;
  why_relevant: string[];
  reasons: string[];
  missing_fields: string[];
  benefits: string | null;
  required_documents: string[];
  application_steps: string[];
  official_url: string | null;
  application_url: string | null;
  last_verified: string | null;
  verification_status: string;
  accepting_applications: boolean | null;
  limitations: string[];
  score: number;
  show_by_default: boolean;
}

export interface RecommendationResponse {
  results: RecommendationCard[];
  counts: Record<string, number>;
  disclaimer: string;
}

export interface SchemeSummary {
  id: string;
  name: string;
  name_ta: string | null;
  jurisdiction: string;
  applicable_state: string;
  category: string;
  beneficiary_types: string[];
  summary: string;
  verification_status: string;
  operational_status: string;
  is_cash_benefit: boolean;
  date_checked: string | null;
  official_url: string | null;
}

export interface SchemeDetail extends SchemeSummary {
  benefits: string | null;
  required_documents: string[];
  application_steps: string[];
  application_url: string | null;
  accepting_applications: boolean | null;
  verification_notes: string | null;
  rules: { key: string; field: string; operator: string; value: unknown; mandatory: boolean; verified: boolean; description: string }[];
  sources: { url: string; title: string | null; source_type: string; verification_status: string; date_checked: string | null }[];
}

export interface SchemePage {
  total: number;
  page: number;
  page_size: number;
  items: SchemeSummary[];
}

export interface Citation {
  ref: string;
  title: string;
  url: string | null;
  page: number | null;
  verified_date: string | null;
  scheme_ids: string[];
}

export interface ChatReply {
  answer: string;
  language: "en" | "ta";
  citations: Citation[];
  clarifying_questions: string[];
  schemes_discussed: string[];
  grounded: boolean;
  llm_used: boolean;
  notice: string | null;
  session_id: string | null;
}
