import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import ErrorBox from "../components/ErrorBox";
import { IconArrow } from "../components/Icons";
import SchemeCard from "../components/SchemeCard";
import Skeleton from "../components/Skeleton";
import { useI18n } from "../i18n";
import { errorMessage, getRecommendations } from "../services/api";
import type { EligibilityStatus, RecommendationResponse } from "../types/api";
import { loadProfile } from "../types/profile";

type Filter = "all" | EligibilityStatus;

export default function Results() {
  const { t } = useI18n();
  const [data, setData] = useState<RecommendationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [showAll, setShowAll] = useState(false);
  const [filter, setFilter] = useState<Filter>("all");
  const profile = loadProfile();

  const load = useCallback(() => {
    const p = loadProfile();
    if (!p) return;
    setLoading(true);
    setError(null);
    getRecommendations(p)
      .then(setData)
      .catch((e) => setError(errorMessage(e)))
      .finally(() => setLoading(false));
  }, []);

  useEffect(load, [load]);

  const all = data?.results ?? [];
  const pool = useMemo(() => all.filter((c) => showAll || c.show_by_default), [all, showAll]);
  const visible = pool.filter((c) => filter === "all" || c.status === filter);
  const hiddenCount = all.filter((c) => !c.show_by_default).length;

  const tabs: { key: Filter; label: string }[] = [
    { key: "all", label: t("filterAll") },
    { key: "potentially_eligible", label: t("sPotentially_eligible") },
    { key: "more_information_required", label: t("sMore_information_required") },
    { key: "information_unverified", label: t("sInformation_unverified") },
    ...(showAll ? [{ key: "does_not_match" as Filter, label: t("sDoes_not_match") }] : []),
  ];
  const count = (k: Filter) => (k === "all" ? pool.length : pool.filter((c) => c.status === k).length);

  if (!profile) {
    return (
      <section className="card mx-auto max-w-lg p-8 text-center">
        <p className="mb-5 text-lg text-ink-soft">{t("noProfile")}</p>
        <Link to="/profile" className="btn-primary">{t("start")} <IconArrow className="h-4 w-4" /></Link>
      </section>
    );
  }

  return (
    <section>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-ink">{t("resultsTitle")}</h1>
          <p className="mt-1.5 text-ink-soft">{t("resultsLead")}</p>
        </div>
        <Link to="/profile" className="btn-secondary">{t("editAnswers")}</Link>
      </div>

      {data && !loading && (
        <div role="group" aria-label="Filter results" className="mt-6 flex flex-wrap gap-2">
          {tabs.map((tb) => {
            const n = count(tb.key);
            const active = filter === tb.key;
            return (
              <button
                key={tb.key}
                type="button"
                aria-pressed={active}
                onClick={() => setFilter(tb.key)}
                disabled={n === 0 && tb.key !== "all"}
                className={`rounded-full border px-3.5 py-1.5 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-40 ${
                  active ? "border-brand-700 bg-brand-700 text-white shadow-sm"
                    : "border-slate-300 bg-white text-ink-soft hover:border-brand-300"}`}
              >
                {`${tb.label} (${n})`}
              </button>
            );
          })}
        </div>
      )}

      <div className="mt-6" aria-live="polite" aria-busy={loading}>
        {loading && (<><p className="mb-4 text-ink-mute">{t("loading")}</p><Skeleton /></>)}
        {error && <ErrorBox message={error} onRetry={load} />}
        {data && !loading && (
          <>
            {visible.length === 0 && (
              <p className="card p-6 text-ink-soft">{t("noResults")}</p>
            )}
            <div className="space-y-5">
              {visible.map((c) => <SchemeCard key={c.scheme_id} card={c} />)}
            </div>
            {hiddenCount > 0 && (
              <button onClick={() => { setShowAll((v) => !v); setFilter("all"); }} className="btn-secondary mt-8">
                {showAll ? t("hideMore") : `${t("showMore")} (${hiddenCount})`}
              </button>
            )}
            <p className="mt-8 rounded-xl border border-slate-200 bg-white/70 p-4 text-sm text-ink-mute">
              {data.disclaimer}
            </p>
          </>
        )}
      </div>
    </section>
  );
}
