import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import ErrorBox from "../components/ErrorBox";
import { IconArrow, IconSearch } from "../components/Icons";
import Skeleton from "../components/Skeleton";
import { useI18n } from "../i18n";
import { errorMessage, listSchemes } from "../services/api";
import type { SchemePage } from "../types/api";

const CATEGORIES = ["scholarship", "pension", "allowance", "concession", "assistive_devices",
  "identity_certification", "financial_assistance", "health_insurance", "ngo_grant", "institutional_grant"];
const AUDIENCES = ["person_with_disability", "student", "child", "senior_citizen", "widow", "farmer",
  "job_seeker", "family_of_person_with_disability", "caregiver"];

const VERIFY_STYLE: Record<string, string> = {
  verified: "border-emerald-200 bg-emerald-50 text-emerald-800",
  partially_verified: "border-amber-200 bg-amber-50 text-amber-900",
  unverified: "border-violet-200 bg-violet-50 text-violet-800",
};

export default function Schemes() {
  const { t, lang } = useI18n();
  const [q, setQ] = useState("");
  const [jurisdiction, setJurisdiction] = useState("");
  const [category, setCategory] = useState("");
  const [audience, setAudience] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<SchemePage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    listSchemes({
      q: q || undefined, jurisdiction: jurisdiction || undefined, category: category || undefined,
      beneficiary_type: audience || undefined, page, page_size: 10,
    })
      .then(setData)
      .catch((e) => setError(errorMessage(e)))
      .finally(() => setLoading(false));
  }, [q, jurisdiction, category, audience, page]);
  useEffect(load, [load]);

  const filter = (set: (v: string) => void) => (v: string) => { setPage(1); set(v); };
  const pages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;

  return (
    <section>
      <h1 className="text-3xl font-extrabold text-ink">{t("schemesTitle")}</h1>

      <form role="search" onSubmit={(e) => e.preventDefault()}
        className="card mt-6 grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-[2fr_1fr_1fr_1fr]">
        <div className="relative">
          <label className="sr-only" htmlFor="q">{t("search")}</label>
          <IconSearch className="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
          <input id="q" className="input !pl-10" placeholder={t("search")} value={q}
            onChange={(e) => filter(setQ)(e.target.value)} />
        </div>
        <select aria-label="Government" className="input" value={jurisdiction}
          onChange={(e) => filter(setJurisdiction)(e.target.value)}>
          <option value="">{t("allJurisdictions")}</option>
          <option value="central">{t("central")}</option>
          <option value="tamil_nadu">{t("tamilNadu")}</option>
        </select>
        <select aria-label={t("category")} className="input" value={category}
          onChange={(e) => filter(setCategory)(e.target.value)}>
          <option value="">{t("allCategories")}</option>
          {CATEGORIES.map((c) => <option key={c} value={c}>{c.replace(/_/g, " ")}</option>)}
        </select>
        <select aria-label={t("beneficiary")} className="input" value={audience}
          onChange={(e) => filter(setAudience)(e.target.value)}>
          <option value="">{t("allAudiences")}</option>
          {AUDIENCES.map((a) => <option key={a} value={a}>{a.replace(/_/g, " ")}</option>)}
        </select>
      </form>

      <div className="mt-6" aria-live="polite" aria-busy={loading}>
        {error && <ErrorBox message={error} onRetry={load} />}
        {loading && !data && <Skeleton />}
        {data && (
          <p className="mb-3 text-sm text-ink-mute">{data.total} {t("resultsCount")}</p>
        )}
        {data && data.items.length === 0 && <p className="card p-6 text-ink-soft">{t("noResults")}</p>}
        <ul className="space-y-3">
          {data?.items.map((s) => (
            <li key={s.id}>
              <Link to={`/schemes/${s.id}`} className="card card-hover group flex items-start gap-4 p-5">
                <div className="min-w-0 flex-1">
                  <div className="mb-2 flex flex-wrap gap-2">
                    <span className="chip border-brand-100 bg-brand-50 text-brand-800">
                      {s.jurisdiction === "tamil_nadu" ? t("tamilNadu") : t("central")}
                    </span>
                    <span className="chip border-slate-200 text-ink-mute">{s.category.replace(/_/g, " ")}</span>
                    <span className={`chip ${VERIFY_STYLE[s.verification_status] ?? ""}`}>
                      {t("verification")}: {s.verification_status.replace("_", " ")}
                    </span>
                  </div>
                  <span className="block text-base font-semibold text-ink group-hover:text-brand-800">
                    {lang === "ta" && s.name_ta ? s.name_ta : s.name}
                  </span>
                  {s.summary && <span className="mt-1 line-clamp-2 block text-sm text-ink-soft">{s.summary}</span>}
                </div>
                <IconArrow className="mt-1 h-5 w-5 shrink-0 text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-brand-700" />
              </Link>
            </li>
          ))}
        </ul>
      </div>

      {data && data.total > data.page_size && (
        <nav aria-label="Pagination" className="mt-8 flex items-center justify-center gap-4">
          <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)} className="btn-secondary">{t("prev")}</button>
          <span className="text-sm text-ink-mute">{t("pageOf")} {page} / {pages}</span>
          <button disabled={page >= pages} onClick={() => setPage((p) => p + 1)} className="btn-secondary">{t("next")}</button>
        </nav>
      )}
    </section>
  );
}
