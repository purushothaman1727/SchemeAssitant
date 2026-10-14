import { useI18n } from "../i18n";

interface Props {
  steps: string[];
  current: number;
  onJump: (index: number) => void;
}

export default function Stepper({ steps, current, onJump }: Props) {
  const { t } = useI18n();
  const pct = Math.round(((current + 1) / steps.length) * 100);
  return (
    <div className="mb-8">
      <div className="mb-3 flex items-baseline justify-between text-sm">
        <span className="font-semibold text-brand-800">
          {t("stepOf")} {current + 1} {t("of")} {steps.length}
        </span>
        <span className="text-ink-mute">{steps[current]}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-200" role="presentation">
        <div className="h-full rounded-full bg-gradient-to-r from-brand-500 to-brand-700 transition-all duration-500"
          style={{ width: `${pct}%` }} />
      </div>
      <ol aria-label="Progress" className="mt-4 hidden items-center gap-1 sm:flex">
        {steps.map((label, i) => (
          <li key={label} className={i === current ? "min-w-0 flex-1" : "shrink-0"}>
            <button
              type="button"
              disabled={i > current}
              onClick={() => onJump(i)}
              aria-current={i === current ? "step" : undefined}
              className={`flex w-full items-center gap-2 rounded-xl px-2 py-1.5 text-left text-sm transition ${
                i === current ? "bg-brand-50 font-semibold text-brand-800"
                  : i < current ? "text-ink-soft hover:bg-slate-100" : "cursor-not-allowed text-slate-400"
              }`}
            >
              <span className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                i <= current ? "bg-brand-700 text-white" : "bg-slate-200 text-slate-500"}`}>
                {i + 1}
              </span>
              <span className={i === current ? "truncate" : "sr-only"}>{label}</span>
            </button>
          </li>
        ))}
      </ol>
    </div>
  );
}
