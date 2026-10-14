import { ReactNode, useState } from "react";
import { UseFormRegisterReturn, useForm } from "react-hook-form";
import { useLocation, useNavigate } from "react-router-dom";
import { IconArrow } from "../components/Icons";
import Stepper from "../components/Stepper";
import { TKey, useI18n } from "../i18n";
import { EMPTY_FORM, ProfileFormValues, saveProfile, toPayload } from "../types/profile";

const STATES = [
  "Tamil Nadu", "Andhra Pradesh", "Karnataka", "Kerala", "Maharashtra", "Delhi",
  "Gujarat", "Uttar Pradesh", "West Bengal", "Other",
];
const DISABILITY_TYPES = ["locomotor", "visual", "hearing", "intellectual", "multiple", "other"] as const;
const CERT: [string, string][] = [
  ["udid", "Holds UDID card"], ["certificate_only", "Has a disability certificate, no UDID"],
  ["none", "No certificate yet"], ["unknown", "Not sure"],
];
const EDUCATION: [string, string][] = [
  ["below_9", "Below class 9"], ["class_9_10", "Class 9 or 10"], ["class_11_12", "Class 11 or 12"],
  ["diploma", "Diploma / certificate course"], ["undergraduate", "Undergraduate degree"],
  ["postgraduate", "Postgraduate degree"], ["doctoral", "M.Phil / PhD"], ["other", "Other"],
];
const STEPS: TKey[] = ["stepApplicant", "stepHousehold", "stepDisability", "stepDetails", "stepReview"];
const LAST = STEPS.length - 1;

const TRI: [keyof ProfileFormValues, TKey][] = [
  ["guardian_has_disability", "qGuardian"], ["is_bpl", "qBpl"], ["is_widow", "qWidow"],
  ["studying_in_notified_institute", "qNotified"], ["registered_unemployed_over_1_year", "qRegistered"],
  ["high_support_need_certified", "qHighSupport"], ["has_listed_chronic_condition", "qListed"],
];

function Choice({ reg, value, children }: { reg: UseFormRegisterReturn; value: string; children: ReactNode }) {
  return (
    <label className="flex cursor-pointer items-start gap-3 rounded-xl border border-slate-200 bg-white p-4 transition
      hover:border-brand-300 has-[:checked]:border-brand-600 has-[:checked]:bg-brand-50 has-[:checked]:shadow-sm">
      <input type="radio" value={value} className="mt-1 h-4 w-4 accent-brand-700" {...reg} />
      <span className="leading-snug text-ink-soft">{children}</span>
    </label>
  );
}

export default function Profile() {
  const { t } = useI18n();
  const nav = useNavigate();
  const loc = useLocation();
  const [step, setStep] = useState(loc.pathname.endsWith("/disability") ? 2 : 0);
  const [error, setError] = useState<string | null>(null);

  const form = useForm<ProfileFormValues>({ mode: "onBlur", defaultValues: EMPTY_FORM });
  const { register, handleSubmit, watch, trigger, formState: { errors } } = form;
  const disability = watch("disability_status");

  const fieldsByStep: (keyof ProfileFormValues)[][] = [
    ["applying_for", "age", "state", "district"],
    ["annual_family_income", "occupation", "education_level", "is_student"],
    ["disability_status", "disability_type", "certificate_status", "disability_percentage"],
    [],
    ["consent_process"],
  ];

  const next = async () => {
    if (await trigger(fieldsByStep[step])) setStep((s) => s + 1);
  };

  const onSubmit = handleSubmit((values) => {
    setError(null);
    if (!saveProfile(toPayload(values))) {
      setError("Could not keep your answers in this browser session. Please enable site storage.");
      return;
    }
    nav("/results");
  });

  const Err = ({ name }: { name: keyof ProfileFormValues }) =>
    errors[name] ? <p role="alert" className="error-text">{t("required")}</p> : null;

  return (
    <div className="mx-auto max-w-2xl">
      <form onSubmit={onSubmit} noValidate className="card p-6 sm:p-9">
        <Stepper steps={STEPS.map(t)} current={step} onJump={setStep} />

        {step === 0 && (
          <fieldset className="space-y-6">
            <div>
              <legend className="mb-3 text-lg font-semibold text-ink">{t("applyingFor")}</legend>
              <div className="grid gap-3 sm:grid-cols-2">
                <Choice reg={register("applying_for")} value="self">{t("forSelf")}</Choice>
                <Choice reg={register("applying_for")} value="child">{t("forChild")}</Choice>
              </div>
            </div>
            <div>
              <label className="field-label">
                {t("age")}
                <input type="number" min={0} max={120} className="input mt-1.5"
                  {...register("age", { required: true, min: 0, max: 120 })} />
              </label>
              <Err name="age" />
            </div>
            <div className="grid gap-6 sm:grid-cols-2">
              <label className="field-label">
                {t("state")}
                <select className="input mt-1.5" {...register("state", { required: true })}>
                  {STATES.map((s) => <option key={s}>{s}</option>)}
                </select>
              </label>
              <label className="field-label">
                {t("district")}
                <input className="input mt-1.5" {...register("district")} />
              </label>
            </div>
          </fieldset>
        )}

        {step === 1 && (
          <fieldset className="space-y-6">
            <label className="field-label">
              {t("income")}
              <input type="number" min={0} className="input mt-1.5" aria-describedby="inc-hint"
                {...register("annual_family_income", { min: 0 })} />
              <span id="inc-hint" className="hint">{t("incomeHint")}</span>
            </label>
            <div className="grid gap-6 sm:grid-cols-2">
              <label className="field-label">
                {t("education")}
                <select className="input mt-1.5" {...register("education_level")}>
                  <option value="">{t("unknown")}</option>
                  {EDUCATION.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </label>
              <label className="field-label">
                {t("isStudent")}
                <select className="input mt-1.5" {...register("is_student")}>
                  <option value="unknown">{t("unknown")}</option>
                  <option value="yes">{t("yes")}</option>
                  <option value="no">{t("no")}</option>
                </select>
              </label>
            </div>
            <label className="field-label">
              {t("occupation")}
              <input className="input mt-1.5" {...register("occupation")} />
            </label>
          </fieldset>
        )}

        {step === 2 && (
          <fieldset className="space-y-4">
            <legend className="mb-1 text-lg font-semibold text-ink">{t("disabilityQ")}</legend>
            <div className="grid gap-3">
              <Choice reg={register("disability_status", { required: true })} value="yes">{t("disYes")}</Choice>
              <Choice reg={register("disability_status", { required: true })} value="no">{t("disNo")}</Choice>
              <Choice reg={register("disability_status", { required: true })} value="prefer_not_to_say">
                {t("disPreferNot")}
              </Choice>
            </div>
            {disability === "yes" && (
              <div className="animate-fade-up space-y-5 rounded-2xl border border-brand-100 bg-brand-50/50 p-5">
                <div>
                  <label className="field-label">
                    {t("disType")}
                    <select className="input mt-1.5" {...register("disability_type", { required: true })}>
                      <option value="">—</option>
                      {DISABILITY_TYPES.map((d) => <option key={d} value={d}>{d}</option>)}
                    </select>
                  </label>
                  <Err name="disability_type" />
                </div>
                <div>
                  <label className="field-label">
                    {t("certStatus")}
                    <select className="input mt-1.5" {...register("certificate_status", { required: true })}>
                      <option value="">—</option>
                      {CERT.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                    </select>
                  </label>
                  <Err name="certificate_status" />
                </div>
                <label className="field-label">
                  {t("pct")}
                  <input type="number" min={0} max={100} className="input mt-1.5"
                    {...register("disability_percentage", { min: 0, max: 100 })} />
                </label>
              </div>
            )}
          </fieldset>
        )}

        {step === 3 && (
          <fieldset className="space-y-5">
            <legend className="text-ink-soft">{t("detailsIntro")}</legend>
            {TRI.map(([name, label]) => (
              <label key={name} className="field-label">
                {t(label)}
                <select className="input mt-1.5" {...register(name)}>
                  <option value="">{t("unknown")}</option>
                  <option value="yes">{t("yes")}</option>
                  <option value="no">{t("no")}</option>
                </select>
              </label>
            ))}
            <label className="field-label">
              {t("qLand")}
              <input type="number" min={0} step="0.1" className="input mt-1.5"
                {...register("land_holding_hectares", { min: 0 })} />
            </label>
          </fieldset>
        )}

        {step === LAST && (
          <fieldset className="space-y-5">
            <p className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-ink-soft">{t("reviewNote")}</p>
            <label className="flex cursor-pointer items-start gap-3 rounded-xl border border-slate-200 p-4 has-[:checked]:border-brand-600 has-[:checked]:bg-brand-50">
              <input type="checkbox" className="mt-1 h-4 w-4 accent-brand-700" {...register("consent_process", { required: true })} />
              <span className="text-ink-soft">{t("consent")}</span>
            </label>
            <Err name="consent_process" />
          </fieldset>
        )}

        {error && <p role="alert" className="error-text mt-4">{error}</p>}

        <div className="mt-9 flex items-center justify-between border-t border-slate-100 pt-6">
          <button type="button" disabled={step === 0} onClick={() => setStep((s) => s - 1)} className="btn-secondary">
            {t("back")}
          </button>
          {step < LAST ? (
            <button key="next" type="button" onClick={next} className="btn-primary">
              {t("next")} <IconArrow className="h-4 w-4" />
            </button>
          ) : (
            <button key="submit" type="submit" className="btn-primary">
              {t("submit")} <IconArrow className="h-4 w-4" />
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
