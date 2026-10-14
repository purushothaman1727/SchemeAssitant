import { useI18n } from "../i18n";
import { IconAlert } from "./Icons";

export default function ErrorBox({ message, onRetry }: { message: string; onRetry?: () => void }) {
  const { t } = useI18n();
  return (
    <div role="alert" className="flex items-start gap-3 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-rose-900">
      <IconAlert className="mt-0.5 h-5 w-5 shrink-0" />
      <div className="flex-1">
        <p className="font-medium">{message}</p>
        {onRetry && (
          <button onClick={onRetry} className="btn-secondary mt-3 !py-1.5">{t("retry")}</button>
        )}
      </div>
    </div>
  );
}
