import { TKey, useI18n } from "../i18n";
import type { EligibilityStatus } from "../types/api";
import { IconAlert, IconCheck, IconQuestion, IconX } from "./Icons";

export const STATUS_STYLE: Record<
  EligibilityStatus,
  { badge: string; accent: string; icon: typeof IconCheck; key: TKey }
> = {
  potentially_eligible: {
    badge: "bg-emerald-50 text-emerald-800 border-emerald-200", accent: "border-l-emerald-500",
    icon: IconCheck, key: "sPotentially_eligible",
  },
  more_information_required: {
    badge: "bg-amber-50 text-amber-900 border-amber-200", accent: "border-l-amber-400",
    icon: IconQuestion, key: "sMore_information_required",
  },
  does_not_match: {
    badge: "bg-slate-100 text-slate-700 border-slate-200", accent: "border-l-slate-300",
    icon: IconX, key: "sDoes_not_match",
  },
  information_unverified: {
    badge: "bg-violet-50 text-violet-800 border-violet-200", accent: "border-l-violet-400",
    icon: IconAlert, key: "sInformation_unverified",
  },
};

/** Status is conveyed by icon + text, never colour alone. */
export default function StatusBadge({ status }: { status: EligibilityStatus }) {
  const { t } = useI18n();
  const s = STATUS_STYLE[status];
  const Icon = s.icon;
  return (
    <span className={`chip ${s.badge} !text-[13px]`}>
      <Icon className="h-3.5 w-3.5" />
      {t(s.key)}
    </span>
  );
}
