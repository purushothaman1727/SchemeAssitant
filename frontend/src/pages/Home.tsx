import { Link } from "react-router-dom";
import { IconArrow, IconDoc, IconGlobe, IconLock, IconSearch, IconShield } from "../components/Icons";
import heroCard from "../assets/hero-card.svg";
import ctaBanner from "../assets/cta-banner.svg";
import schemeCard from "../assets/scheme-card.svg";
import StatusBadge from "../components/StatusBadge";
import { useI18n } from "../i18n";

export default function Home() {
  const { t } = useI18n();

  const steps = [
    { icon: IconSearch, title: t("how1t"), body: t("how1b") },
    { icon: IconShield, title: t("how2t"), body: t("how2b") },
    { icon: IconDoc, title: t("how3t"), body: t("how3b") },
  ];
  const trust = [
    { icon: IconShield, title: t("trust1t"), body: t("trust1b") },
    { icon: IconLock, title: t("trust2t"), body: t("trust2b") },
    { icon: IconGlobe, title: t("trust3t"), body: t("trust3b") },
  ];

  return (
    <div>
      {/* hero: full-bleed powder blue with a soft still-life illustration */}
      <section className="bg-sky-300">
        <div className="mx-auto grid max-w-6xl items-center gap-10 px-4 py-12 sm:px-6 lg:grid-cols-[1.05fr_.95fr] lg:py-16">
          <div>
            <p className="section-title !text-navy-700">{t("heroEyebrow")}</p>
            <h1 className="mt-4 text-3xl font-semibold leading-[1.15] sm:text-5xl sm:leading-[1.1]">{t("homeTitle")}</h1>
            <p className="mt-5 max-w-xl text-lg leading-relaxed text-navy-800">{t("homeLead")}</p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Link to="/profile" className="btn-primary btn-lg">
                {t("start")} <IconArrow className="h-5 w-5" />
              </Link>
              <Link to="/schemes" className="btn btn-lg bg-white text-navy hover:bg-paper">{t("navSchemes")}</Link>
            </div>
            <p className="mt-4 text-sm text-navy-700">{t("heroSub")}</p>
          </div>
          <div aria-hidden="true" className="overflow-hidden rounded-3xl bg-white/40 shadow-lift">
            <img src={heroCard} alt="" width={600} height={430} className="block h-auto w-full" />
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-6xl space-y-16 px-4 py-14 sm:space-y-20 sm:px-6 sm:py-20">
        <section aria-labelledby="how-title">
          <h2 id="how-title" className="display-title">{t("howTitle")}</h2>
          <ol className="mt-8 grid gap-5 md:grid-cols-3">
            {steps.map((s, i) => (
              <li key={s.title} className="card card-hover relative p-6">
                <span className="absolute right-5 top-4 font-display text-5xl font-semibold text-sky-200" aria-hidden="true">{i + 1}</span>
                <span className="flex h-11 w-11 items-center justify-center rounded-full bg-sky-100 text-navy">
                  <s.icon className="h-6 w-6" />
                </span>
                <h3 className="mt-4 text-lg font-semibold text-ink">{s.title}</h3>
                <p className="mt-1.5 leading-relaxed text-ink-soft">{s.body}</p>
              </li>
            ))}
          </ol>
        </section>

        {/* status legend: shows exactly what results look like, with the real badge component */}
        <section aria-hidden="true" className="grid items-center overflow-hidden rounded-3xl border border-navy-100 bg-white shadow-card md:grid-cols-2">
          <div className="space-y-3 p-8 sm:p-12">
            {(["potentially_eligible", "more_information_required", "information_unverified", "does_not_match"] as const).map((s, i) => (
              <div key={s} className="flex items-center justify-between rounded-2xl border border-navy-100 bg-paper p-4" style={{ opacity: 1 - i * 0.1 }}>
                <div className="space-y-2">
                  <div className="h-2.5 rounded-full bg-navy-200" style={{ width: `${150 - i * 20}px` }} />
                  <div className="h-2 w-24 rounded-full bg-navy-100" />
                </div>
                <StatusBadge status={s} />
              </div>
            ))}
          </div>
          <img src={schemeCard} alt="" width={600} height={520} className="block h-full min-h-[260px] w-full object-cover" />
        </section>

        <section className="rounded-3xl bg-sky-300 p-8 sm:p-12" aria-label="Why trust this">
          <div className="grid gap-8 md:grid-cols-3">
            {trust.map((x) => (
              <div key={x.title}>
                <span className="mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-white text-navy">
                  <x.icon className="h-5 w-5" />
                </span>
                <h3 className="text-lg font-semibold text-navy">{x.title}</h3>
                <p className="mt-1.5 leading-relaxed text-navy-800">{x.body}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="relative flex flex-col-reverse overflow-hidden rounded-3xl border border-navy-100 bg-[#d9eaf0] shadow-card md:block md:min-h-[360px]">
          <img src={ctaBanner} alt="" aria-hidden="true" width={1200} height={475}
            className="pointer-events-none block h-auto w-full md:absolute md:inset-0 md:h-full md:object-cover md:object-right" />
          <div className="relative p-8 sm:p-12 md:max-w-[50%]">
            <h2 className="display-title">{t("homeTitle")}</h2>
            <p className="mt-3 max-w-md text-ink-soft">{t("heroSub")}</p>
            <Link to="/schemes" className="btn-primary mt-6">{t("navFind")}</Link>
          </div>
        </section>
      </div>
    </div>
  );
}
