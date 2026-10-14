import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import ErrorBox from "../components/ErrorBox";
import { IconChat, IconCheck, IconClock, IconExternal } from "../components/Icons";
import Skeleton from "../components/Skeleton";
import { useI18n } from "../i18n";
import { errorMessage, getScheme } from "../services/api";
import type { SchemeDetail as Detail } from "../types/api";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="card p-6">
      <h2 className="mb-3 text-lg font-semibold text-ink">{title}</h2>
      {children}
    </section>
  );
}

export default function SchemeDetail() {
  const { id = "" } = useParams();
  const { t, lang } = useI18n();
  const [s, setS] = useState<Detail | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setError(null);
    getScheme(id).then(setS).catch((e) => setError(errorMessage(e)));
  }, [id]);
  useEffect(load, [load]);

  if (error) return <ErrorBox message={error} onRetry={load} />;
  if (!s) return <Skeleton rows={2} />;

  const list = (items: string[]) =>
    items.length ? (
      <ul className="space-y-2 text-ink-soft">
        {items.map((x) => (
          <li key={x} className="flex gap-2.5">
            <IconCheck className="mt-0.5 h-5 w-5 shrink-0 text-brand-600" />
            <span>{x}</span>
          </li>
        ))}
      </ul>
    ) : <p className="text-ink-mute">{t("noneRecorded")}</p>;

  return (
    <article>
      <Link to="/schemes" className="link text-sm">← {t("navSchemes")}</Link>
      <div className="mt-4 grid gap-6 lg:grid-cols-[1fr_20rem]">
        <div className="space-y-5">
          <header>
            <div className="mb-3 flex flex-wrap gap-2">
              <span className="chip border-brand-100 bg-brand-50 text-brand-800">
                {s.jurisdiction === "tamil_nadu" ? t("tamilNadu") : t("central")}
              </span>
              <span className="chip border-slate-200 bg-white text-ink-mute">{s.category.replace(/_/g, " ")}</span>
            </div>
            <h1 className="text-3xl font-extrabold leading-tight text-ink">
              {lang === "ta" && s.name_ta ? s.name_ta : s.name}
            </h1>
            <p className="mt-3 text-lg leading-relaxed text-ink-soft">{s.summary}</p>
          </header>

          {!s.is_cash_benefit && (
            <p className="rounded-xl border border-brand-100 bg-brand-50 p-4 text-brand-900">
              This is not a direct cash-benefit scheme.
            </p>
          )}

          <Section title={t("benefits")}><p className="leading-relaxed text-ink-soft">{s.benefits ?? t("noneRecorded")}</p></Section>
          <Section title={t("documents")}>{list(s.required_documents)}</Section>
          <Section title={t("steps")}>{list(s.application_steps)}</Section>

          <Section title={t("rulesTitle")}>
            {s.rules.length === 0 ? <p className="text-ink-mute">{t("noneRecorded")}</p> : (
              <ul className="space-y-3">
                {s.rules.map((r) => (
                  <li key={r.key} className="flex flex-wrap items-start justify-between gap-2 text-ink-soft">
                    <span className="max-w-prose">{r.description}</span>
                    <span className={`chip ${r.verified ? "border-emerald-200 bg-emerald-50 text-emerald-800"
                      : "border-amber-200 bg-amber-50 text-amber-900"}`}>
                      {r.verified ? t("verifiedRule") : t("unverifiedRule")}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </Section>

          {s.verification_notes && (
            <Section title={t("notesTitle")}>
              <p className="text-sm leading-relaxed text-ink-soft">{s.verification_notes}</p>
            </Section>
          )}
        </div>

        <aside className="space-y-5 lg:sticky lg:top-24 lg:self-start">
          <div className="card space-y-4 p-6">
            <div>
              <p className="section-title">{t("verification")}</p>
              <p className="mt-1 font-semibold capitalize text-ink">{s.verification_status.replace("_", " ")}</p>
            </div>
            {s.date_checked && (
              <p className="flex items-center gap-2 text-sm text-ink-mute">
                <IconClock className="h-4 w-4" /> {t("lastVerified")}: {s.date_checked}
              </p>
            )}
            {s.application_url && (
              <a className="btn-primary w-full" href={s.application_url} target="_blank" rel="noopener noreferrer">
                {t("applyLink")} <IconExternal className="h-4 w-4" />
              </a>
            )}
            <Link className="btn-secondary w-full" to={`/chat?scheme=${s.id}`}>
              <IconChat className="h-4 w-4" /> {t("askChat")}
            </Link>
          </div>

          <div className="card p-6">
            <h2 className="mb-3 text-lg font-semibold text-ink">{t("sourcesTitle")}</h2>
            <ul className="space-y-3">
              {s.sources.map((x) => (
                <li key={x.url} className="text-sm">
                  <a className="link break-all" href={x.url} target="_blank" rel="noopener noreferrer">
                    {x.title ?? x.url}
                  </a>
                  <span className="ml-1.5 text-xs text-ink-mute">({x.verification_status})</span>
                </li>
              ))}
            </ul>
          </div>
        </aside>
      </div>
    </article>
  );
}
