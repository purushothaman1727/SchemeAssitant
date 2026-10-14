import { FormEvent, useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { IconSend, IconSpark, LogoMark } from "../components/Icons";
import RichText from "../components/RichText";
import { useI18n } from "../i18n";
import { ChatTurn, deleteChatSession, errorMessage, sendChat } from "../services/api";
import type { Citation } from "../types/api";
import { loadProfile } from "../types/profile";

interface Msg {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  clarifying?: string[];
  notice?: string | null;
  error?: boolean;
}

export default function Chat() {
  const { t, lang } = useI18n();
  const [params] = useSearchParams();
  const profile = loadProfile();
  const [messages, setMessages] = useState<Msg[]>([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [usePersonal, setUsePersonal] = useState(profile !== null);
  const [saveChat, setSaveChat] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [answerLang, setAnswerLang] = useState<"auto" | "en" | "ta">("auto");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => { endRef.current?.scrollIntoView?.({ behavior: "smooth", block: "end" }); }, [messages, busy]);

  const send = async (content: string) => {
    const trimmed = content.trim();
    if (!trimmed || busy) return;
    const history: ChatTurn[] = messages.filter((m) => !m.error).slice(-10)
      .map((m) => ({ role: m.role, content: m.content }));
    setMessages((m) => [...m, { role: "user", content: trimmed }]);
    setText("");
    setBusy(true);
    try {
      const r = await sendChat({
        message: trimmed, language: answerLang, profile: usePersonal ? profile : null,
        history, store_history: saveChat, session_id: sessionId,
      });
      if (r.session_id) setSessionId(r.session_id);
      setMessages((m) => [...m, {
        role: "assistant", content: r.answer, citations: r.citations,
        clarifying: r.clarifying_questions, notice: r.notice,
      }]);
    } catch (e) {
      setMessages((m) => [...m, { role: "assistant", content: errorMessage(e), error: true }]);
    } finally {
      setBusy(false);
    }
  };

  const onSubmit = (e: FormEvent) => { e.preventDefault(); void send(text); };

  const removeSaved = async () => {
    if (!sessionId) return;
    try { await deleteChatSession(sessionId); } catch { /* the local view is cleared either way */ }
    setSessionId(null);
    setSaveChat(false);
    setMessages([]);
  };

  const preset = params.get("scheme");
  const suggestions = [t("sugg1"), t("sugg2"), t("sugg3")];

  return (
    <section className="mx-auto max-w-3xl">
      <div className="mb-5 flex items-center gap-3">
        <LogoMark className="h-11 w-11" />
        <div>
          <h1 className="text-2xl font-extrabold text-ink">{t("chatTitle")}</h1>
          <p className="text-sm text-ink-mute">{t("chatIntro")}</p>
        </div>
      </div>

      <div className="card mb-4 flex flex-wrap items-center gap-x-6 gap-y-3 px-4 py-3 text-sm">
        {profile && (
          <label className="flex cursor-pointer items-center gap-2 text-ink-soft">
            <input type="checkbox" className="h-4 w-4 accent-brand-700" checked={usePersonal}
              onChange={(e) => setUsePersonal(e.target.checked)} />
            {t("usingProfile")}
          </label>
        )}
        <label className="flex cursor-pointer items-center gap-2 text-ink-soft">
          <input type="checkbox" className="h-4 w-4 accent-brand-700" checked={saveChat}
            onChange={(e) => setSaveChat(e.target.checked)} />
          {t("saveChat")}
        </label>
        <label className="flex items-center gap-2 text-ink-soft">
          {t("answerLang")}
          <select className="input !w-auto !py-1.5 text-sm" value={answerLang}
            onChange={(e) => setAnswerLang(e.target.value as "auto" | "en" | "ta")}>
            <option value="auto">{t("langAuto")}</option>
            <option value="en">English</option>
            <option value="ta">தமிழ்</option>
          </select>
        </label>
        {sessionId && (
          <button onClick={removeSaved} className="font-medium text-rose-700 underline underline-offset-4">
            {t("deleteChat")}
          </button>
        )}
      </div>

      <div className="card flex min-h-[26rem] flex-col">
        <div role="log" aria-live="polite" aria-label="Conversation" className="flex-1 space-y-5 p-4 sm:p-6">
          {messages.length === 0 && (
            <div className="py-6 text-center">
              <span className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-50 text-brand-700">
                <IconSpark className="h-6 w-6" />
              </span>
              <p className="mb-4 font-medium text-ink-soft">{t("suggTitle")}</p>
              <div className="flex flex-wrap justify-center gap-2">
                {preset && (
                  <button className="chip border-brand-200 bg-brand-50 !px-3.5 !py-2 !text-sm text-brand-800 hover:bg-brand-100"
                    onClick={() => send(lang === "ta" ? "இந்தத் திட்டத்தைப் பற்றி விளக்குங்கள்"
                      : `Explain the scheme ${preset.replace(/-/g, " ")}`)}>
                    {lang === "ta" ? "இந்தத் திட்டத்தைப் பற்றி விளக்குங்கள்" : `Explain: ${preset.replace(/-/g, " ")}`}
                  </button>
                )}
                {suggestions.map((s) => (
                  <button key={s} onClick={() => send(s)}
                    className="chip border-slate-200 bg-white !px-3.5 !py-2 !text-sm text-ink-soft hover:border-brand-300 hover:bg-brand-50">
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={`flex gap-3 animate-fade-up ${m.role === "user" ? "flex-row-reverse" : ""}`}>
              {m.role === "assistant"
                ? <LogoMark className="mt-0.5 h-8 w-8 shrink-0" />
                : <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-slate-200 text-xs font-bold text-ink-soft" aria-hidden="true">
                    {t("you").slice(0, 1)}
                  </span>}
              <div className={`min-w-0 max-w-[85%] ${m.role === "user" ? "text-right" : ""}`}>
                <div
                  data-msg={m.role}
                  className={`inline-block whitespace-pre-wrap rounded-2xl px-4 py-3 text-left leading-relaxed ${
                    m.role === "user" ? "rounded-tr-md bg-brand-700 text-white"
                      : m.error ? "rounded-tl-md border border-rose-200 bg-rose-50 text-rose-900"
                        : "rounded-tl-md bg-slate-100 text-ink"}`}>
                  {m.role === "assistant" && !m.error ? <RichText text={m.content} /> : m.content}
                </div>

                {m.citations && m.citations.length > 0 && (
                  <div className="mt-2 flex flex-wrap items-center gap-x-2 gap-y-1.5 text-xs text-ink-mute">
                    <span className="font-semibold">{t("sources")}: </span>
                    {m.citations.map((c) => (
                      <span key={c.ref} className="chip border-slate-200 bg-white !py-0.5">
                        <span className="font-semibold text-brand-800">[{c.ref}]</span>
                        {c.url ? <a className="link !no-underline" href={c.url} target="_blank" rel="noopener noreferrer">{c.title}</a> : c.title}
                        {c.page ? <span>p.{c.page}</span> : null}
                        {c.verified_date ? <span>({c.verified_date})</span> : null}
                      </span>
                    ))}
                  </div>
                )}

                {m.clarifying && m.clarifying.length > 0 && (
                  <div className="mt-3 rounded-xl border border-amber-200 bg-amber-50 p-3 text-left text-sm text-amber-900">
                    <p className="font-semibold">{t("moreInfoNeeded")}</p>
                    <ul className="mt-1 list-disc space-y-0.5 pl-5">{m.clarifying.map((q) => <li key={q}>{q}</li>)}</ul>
                  </div>
                )}
                {m.notice && <p className="mt-2 text-xs text-ink-mute">{m.notice}</p>}
              </div>
            </div>
          ))}

          {busy && (
            <div className="flex items-center gap-3" role="status">
              <LogoMark className="h-8 w-8 shrink-0" />
              <span className="inline-flex items-center gap-1 rounded-2xl rounded-tl-md bg-slate-100 px-4 py-3">
                {[0, 1, 2].map((d) => (
                  <span key={d} className="h-2 w-2 animate-dot rounded-full bg-slate-400" style={{ animationDelay: `${d * 0.16}s` }} />
                ))}
                <span className="sr-only">{t("thinking")}</span>
              </span>
            </div>
          )}
          <div ref={endRef} />
        </div>

        <form onSubmit={onSubmit} className="flex gap-2 border-t border-slate-100 bg-slate-50/60 p-3 sm:p-4">
          <label className="sr-only" htmlFor="chat-input">{t("chatPlaceholder")}</label>
          <input id="chat-input" value={text} maxLength={1000} onChange={(e) => setText(e.target.value)}
            placeholder={t("chatPlaceholder")} className="input flex-1" autoComplete="off" />
          <button type="submit" disabled={busy || !text.trim()} className="btn-primary">
            <IconSend className="h-4 w-4" /> {t("send")}
          </button>
        </form>
      </div>
    </section>
  );
}
