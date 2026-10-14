import { Link } from "react-router-dom";
import { useI18n } from "../i18n";
import { FIELD_LABELS } from "../lib/fieldLabels";
import type { RecommendationCard } from "../types/api";
import { IconArrow, IconChat, IconClock, IconExternal } from "./Icons";
import StatusBadge, { STATUS_STYLE } from "./StatusBadge";

function Block({ title, items }: { title: string; items: string[] }) {
  if (!items.length) return null;
  return (
    <div>
      <h4 className="section-title mb-1.5">{title}</h4>
      <ul className="space-y-1.5 text-sm leading-relaxed text-ink-soft">
        {items.map((x) => (
          <li key={x} className="flex gap-2">
            <span aria-hidden="true" className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-slate-300" />
            <span>{x}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function SchemeCard({ card }: { card: RecommendationCard }) {
  const { t, lang } = useI18n();
  const title = lang === "ta" && card.name_ta ? card.name_ta : card.name;
  const missing = card.missing_fields.map((f) => FIELD_LABELS[f]?.[lang] ?? f);
  const accent = STATUS_STYLE[card.status].accent;

  return (
    <article
      className={`card card-hover overflow-hidden border-l-4 ${accent} animate-fade-up`}
      aria-labelledby={`h-${card.scheme_id}`}
    >
      <div className="p-5 sm:p-6">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <span className="chip border-brand-100 bg-brand-50 text-brand-800">
            {card.jurisdiction === "tamil_nadu" ? t("tamilNadu") : t("central")}
          </span>
          <span className="chip border-slate-200 bg-white text-ink-mute">{card.category.replace(/_/g, " ")}</span>
          <span className="ml-auto"><StatusBadge status={card.status} /></span>
        </div>

        <h3 id={`h-${card.scheme_id}`} className="text-lg font-semibold leading-snug text-ink">{title}</h3>

        <div className="mt-5 grid gap-6 md:grid-cols-2">
          <Block title={t("whyStatus")} items={card.reasons} />
          <Block title={t("whyRelevant")} items={card.why_relevant} />
          <Block title={t("missingInfo")} items={missing} />
          <div>
            <h4 className="section-title mb-1.5">{t("benefits")}</h4>
            <p className="text-sm leading-relaxed text-ink-soft">{card.benefits ?? t("noneRecorded")}</p>
          </div>
          <Block title={t("documents")} items={card.required_documents} />
          <Block title={t("steps")} items={card.application_steps} />
        </div>

        {card.limitations.length > 0 && (
          <div className="mt-5 rounded-xl border border-amber-200/80 bg-amber-50/60 p-4">
            <Block title={t("limitations")} items={card.limitations} />
          </div>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-2 border-t border-slate-100 bg-slate-50/70 px-5 py-3.5 sm:px-6">
        {card.official_url && (
          <a className="btn-secondary !py-2" href={card.official_url} target="_blank" rel="noopener noreferrer">
            {t("officialSource")} <IconExternal className="h-4 w-4" />
          </a>
        )}
        {card.application_url && (
          <a className="btn-primary !py-2" href={card.application_url} target="_blank" rel="noopener noreferrer">
            {t("applyLink")} <IconExternal className="h-4 w-4" />
          </a>
        )}
        <Link className="btn-ghost !py-2" to={`/schemes/${card.scheme_id}`}>
          {t("details")} <IconArrow className="h-4 w-4" />
        </Link>
        <Link className="btn-ghost !py-2" to={`/chat?scheme=${card.scheme_id}`}>
          <IconChat className="h-4 w-4" /> {t("askChat")}
        </Link>
        {card.last_verified && (
          <span className="ml-auto inline-flex items-center gap-1.5 text-xs text-ink-mute">
            <IconClock className="h-3.5 w-3.5" />
            {t("lastVerified")}: {card.last_verified}
          </span>
        )}
      </div>
    </article>
  );
}
