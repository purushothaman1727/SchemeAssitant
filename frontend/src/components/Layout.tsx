import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { TKey, useI18n } from "../i18n";
import { IconInfo, IconMenu, IconX, LogoMark } from "./Icons";

const NAV: { to: string; key: TKey; end?: boolean }[] = [
  { to: "/", key: "navHome", end: true },
  { to: "/profile", key: "navFind" },
  { to: "/schemes", key: "navSchemes" },
  { to: "/chat", key: "navChat" },
  { to: "/privacy", key: "navPrivacy" },
];

export default function Layout() {
  const { t, lang, setLang } = useI18n();
  const [open, setOpen] = useState(false);
  const loc = useLocation();
  useEffect(() => setOpen(false), [loc.pathname]);

  const link = ({ isActive }: { isActive: boolean }) =>
    `border-b-2 px-1 py-2 text-sm font-medium transition ${
      isActive ? "border-navy text-navy" : "border-transparent text-ink-soft hover:border-sky-500 hover:text-navy"}`;

  const langSwitch = (
    <div role="group" aria-label="Language" className="inline-flex rounded-full border border-navy-200 bg-white/70 p-0.5">
      {(["en", "ta"] as const).map((l) => (
        <button
          key={l}
          onClick={() => setLang(l)}
          aria-pressed={lang === l}
          className={`rounded-full px-3.5 py-1.5 text-sm font-medium transition ${
            lang === l ? "bg-navy text-white" : "text-ink-mute hover:text-navy"
          }`}
        >
          {l === "en" ? "English" : "தமிழ்"}
        </button>
      ))}
    </div>
  );

  return (
    <div className="flex min-h-screen flex-col">
      <a href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-3 focus:top-3 focus:z-50 focus:rounded-full focus:bg-white focus:px-4 focus:py-2 focus:shadow-lift">
        {t("skipToContent")}
      </a>

      <div role="note" className="bg-navy text-white">
        <p className="container-page flex items-start gap-2 py-1.5 text-[12px] leading-snug">
          <IconInfo className="mt-0.5 h-3.5 w-3.5 shrink-0 text-sky-300" />
          <span className="text-navy-100">{t("independent")}</span>
        </p>
      </div>

      <header className="sticky top-0 z-40 border-b border-navy-100 bg-paper/90 backdrop-blur-md">
        <nav aria-label="Main" className="container-page flex items-center gap-2 py-3 sm:gap-4">
          <Link to="/" className="mr-1 flex min-w-0 shrink items-center gap-3 rounded-full">
            <LogoMark className="h-9 w-9 shrink-0" />
            <span className="truncate font-display text-[17px] font-semibold text-navy max-[479px]:sr-only">{t("appName")}</span>
          </Link>

          <div className="ml-4 hidden items-center gap-6 md:flex">
            {NAV.map((n) => (
              <NavLink key={n.to} to={n.to} end={n.end} className={link}>{t(n.key)}</NavLink>
            ))}
          </div>

          <div className="ml-auto flex items-center gap-2">
            {langSwitch}
            <button
              type="button"
              className="btn-secondary !px-3 md:hidden"
              aria-expanded={open}
              aria-controls="mobile-menu"
              aria-label={t("menu")}
              onClick={() => setOpen((v) => !v)}
            >
              {open ? <IconX /> : <IconMenu />}
            </button>
          </div>
        </nav>
        {open && (
          <div id="mobile-menu" className="border-t border-navy-100 bg-paper md:hidden">
            <div className="container-page flex flex-col gap-1 py-3">
              {NAV.map((n) => (
                <NavLink key={n.to} to={n.to} end={n.end} className={link}>{t(n.key)}</NavLink>
              ))}
            </div>
          </div>
        )}
      </header>

      <main id="main" className={`page-enter flex-1 ${loc.pathname === "/" ? "" : "mx-auto w-full max-w-6xl px-4 py-8 sm:py-12"}`}>
        <Outlet />
      </main>

      <footer className="border-t border-navy-100 bg-paper">
        <div className="container-page grid gap-8 py-12 md:grid-cols-[1.4fr_1fr_1fr]">
          <div>
            <span className="flex items-center gap-3">
              <LogoMark className="h-9 w-9" />
              <span className="font-display text-[17px] font-semibold text-navy">{t("appName")}</span>
            </span>
            <p className="mt-4 max-w-sm text-sm leading-relaxed text-ink-soft">{t("footerNote")}</p>
          </div>
          <ul className="space-y-2.5 text-sm text-ink-soft">
            {NAV.slice(0, 3).map((n) => (
              <li key={n.to}><Link className="hover:text-navy hover:underline" to={n.to}>{t(n.key)}</Link></li>
            ))}
          </ul>
          <ul className="space-y-2.5 text-sm text-ink-soft">
            {NAV.slice(3).map((n) => (
              <li key={n.to}><Link className="hover:text-navy hover:underline" to={n.to}>{t(n.key)}</Link></li>
            ))}
          </ul>
        </div>
      </footer>
    </div>
  );
}
