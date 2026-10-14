import type { ProfilePayload } from "./api";

export type Tri = "" | "yes" | "no";

export interface ProfileFormValues {
  applying_for: "self" | "child";
  age: number | string;
  state: string;
  district: string;
  annual_family_income: number | string;
  occupation: string;
  education_level: string;
  is_student: "yes" | "no" | "unknown";
  disability_status: "yes" | "no" | "prefer_not_to_say";
  disability_type: string;
  certificate_status: string;
  disability_percentage: number | string;
  guardian_has_disability: Tri;
  is_bpl: Tri;
  is_widow: Tri;
  land_holding_hectares: number | string;
  studying_in_notified_institute: Tri;
  registered_unemployed_over_1_year: Tri;
  high_support_need_certified: Tri;
  has_listed_chronic_condition: Tri;
  consent_process: boolean;
}

export const EMPTY_FORM: ProfileFormValues = {
  applying_for: "self", age: "", state: "Tamil Nadu", district: "", annual_family_income: "",
  occupation: "", education_level: "", is_student: "unknown", disability_status: "prefer_not_to_say",
  disability_type: "", certificate_status: "", disability_percentage: "",
  guardian_has_disability: "", is_bpl: "", is_widow: "", land_holding_hectares: "",
  studying_in_notified_institute: "", registered_unemployed_over_1_year: "",
  high_support_need_certified: "", has_listed_chronic_condition: "", consent_process: false,
};

const num = (v: number | string): number | null => {
  if (v === "" || v === null || v === undefined) return null;
  const n = typeof v === "number" ? v : Number(v);
  return Number.isFinite(n) ? n : null;
};
const tri = (v: Tri): boolean | null => (v === "yes" ? true : v === "no" ? false : null);
const str = (v: string): string | null => (v.trim() ? v.trim() : null);

/** Maps the form to the API payload. Disability details are sent only when the answer is "yes". */
export function toPayload(f: ProfileFormValues): ProfilePayload {
  const dis = f.disability_status === "yes";
  return {
    applying_for: f.applying_for,
    age: num(f.age),
    state: str(f.state),
    district: str(f.district),
    annual_family_income: num(f.annual_family_income),
    occupation: str(f.occupation),
    education_level: str(f.education_level),
    is_student: f.is_student,
    disability_status: f.disability_status,
    disability_type: dis ? str(f.disability_type) : null,
    certificate_status: dis ? str(f.certificate_status) : null,
    disability_percentage: dis ? num(f.disability_percentage) : null,
    guardian_has_disability: tri(f.guardian_has_disability),
    is_bpl: tri(f.is_bpl),
    is_widow: tri(f.is_widow),
    land_holding_hectares: num(f.land_holding_hectares),
    studying_in_notified_institute: tri(f.studying_in_notified_institute),
    registered_unemployed_over_1_year: tri(f.registered_unemployed_over_1_year),
    high_support_need_certified: tri(f.high_support_need_certified),
    has_listed_chronic_condition: tri(f.has_listed_chronic_condition),
  };
}

const KEY = "profile.v1";

export function saveProfile(p: ProfilePayload): boolean {
  try {
    sessionStorage.setItem(KEY, JSON.stringify(p));
    return true;
  } catch {
    return false;
  }
}

export function loadProfile(): ProfilePayload | null {
  try {
    const raw = sessionStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as ProfilePayload) : null;
  } catch {
    return null;
  }
}

export function clearProfile(): void {
  try {
    sessionStorage.removeItem(KEY);
  } catch {
    /* storage unavailable */
  }
}
