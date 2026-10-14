import { FormEvent, useCallback, useEffect, useState } from "react";
import ErrorBox from "../components/ErrorBox";
import { IconLock } from "../components/Icons";
import { errorMessage, getScheme, listSchemes } from "../services/api";
import {
  JobRow, SchemePatch, SourcePage, listJobs, listSources, login, patchScheme, startIngest,
} from "../services/admin";
import type { SchemeDetail, SchemeSummary } from "../types/api";

// Operator tool, English only. The access token lives in component state: it is never written
// to localStorage/sessionStorage, so a refresh logs out.

const STATUS_CHIP: Record<string, string> = {
  completed: "border-emerald-200 bg-emerald-50 text-emerald-800",
  completed_with_errors: "border-amber-200 bg-amber-50 text-amber-900",
  failed: "border-rose-200 bg-rose-50 text-rose-800",
  running: "border-brand-200 bg-brand-50 text-brand-800",
};

function Login({ onToken }: { onToken: (t: string) => void }) {
  const [u, setU] = useState("");
  const [p, setP] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      onToken((await login(u, p)).access_token);
    } catch (x) {
      setErr(errorMessage(x));
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit} className="card mx-auto max-w-sm space-y-5 p-8">
      <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-50 text-brand-700">
        <IconLock className="h-6 w-6" />
      </span>
      <h1 className="text-2xl font-extrabold text-ink">Administrator sign-in</h1>
      <label className="field-label">Username
        <input className="input mt-1.5" autoComplete="username" value={u} onChange={(e) => setU(e.target.value)} />
      </label>
      <label className="field-label">Password
        <input type="password" className="input mt-1.5" autoComplete="current-password"
          value={p} onChange={(e) => setP(e.target.value)} />
      </label>
      {err && <p role="alert" className="error-text">{err}</p>}
      <button disabled={busy || !u || !p} className="btn-primary w-full">Sign in</button>
    </form>
  );
}

function SchemeEditor({ token }: { token: string }) {
  const [schemes, setSchemes] = useState<SchemeSummary[]>([]);
  const [id, setId] = useState("");
  const [s, setS] = useState<SchemeDetail | null>(null);
  const [form, setForm] = useState<SchemePatch>({});
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    listSchemes({ page_size: 100 }).then((p) => setSchemes(p.items)).catch((e) => setErr(errorMessage(e)));
  }, []);

  useEffect(() => {
    if (!id) return;
    setMsg(null);
    setErr(null);
    getScheme(id).then((d) => {
      setS(d);
      setForm({
        operational_status: d.operational_status, verification_status: d.verification_status,
        accepting_applications: d.accepting_applications, date_checked: d.date_checked,
        verification_notes: d.verification_notes, benefits: d.benefits,
      });
    }).catch((e) => setErr(errorMessage(e)));
  }, [id]);

  const save = async () => {
    setMsg(null);
    setErr(null);
    try {
      await patchScheme(token, id, form);
      setMsg("Saved.");
    } catch (e) {
      setErr(errorMessage(e));
    }
  };

  return (
    <section className="card space-y-4 p-6">
      <h2 className="text-lg font-semibold text-ink">Edit scheme status</h2>
      <p className="text-sm text-ink-mute">
        Only change these after reading the official source. Rule edits and new schemes are available
        through the API (see README).
      </p>
      <select aria-label="Scheme" className="input" value={id} onChange={(e) => setId(e.target.value)}>
        <option value="">Select a scheme…</option>
        {schemes.map((x) => <option key={x.id} value={x.id}>{x.name.slice(0, 90)}</option>)}
      </select>
      {s && (
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="field-label">Operational status
            <select className="input mt-1.5" value={form.operational_status ?? ""}
              onChange={(e) => setForm({ ...form, operational_status: e.target.value })}>
              {["active", "discontinued", "renamed", "unverified"].map((v) => <option key={v}>{v}</option>)}
            </select>
          </label>
          <label className="field-label">Verification status
            <select className="input mt-1.5" value={form.verification_status ?? ""}
              onChange={(e) => setForm({ ...form, verification_status: e.target.value })}>
              {["verified", "partially_verified", "unverified"].map((v) => <option key={v}>{v}</option>)}
            </select>
          </label>
          <label className="field-label">Accepting applications
            <select className="input mt-1.5"
              value={form.accepting_applications === null || form.accepting_applications === undefined ? "" : String(form.accepting_applications)}
              onChange={(e) => setForm({ ...form, accepting_applications: e.target.value === "" ? null : e.target.value === "true" })}>
              <option value="">Unknown</option><option value="true">Yes</option><option value="false">No</option>
            </select>
          </label>
          <label className="field-label">Date checked
            <input type="date" className="input mt-1.5" value={form.date_checked ?? ""}
              onChange={(e) => setForm({ ...form, date_checked: e.target.value || null })} />
          </label>
          <label className="field-label sm:col-span-2">Benefits (verified text only)
            <textarea className="input mt-1.5" rows={2} value={form.benefits ?? ""}
              onChange={(e) => setForm({ ...form, benefits: e.target.value || null })} />
          </label>
          <label className="field-label sm:col-span-2">Verification notes
            <textarea className="input mt-1.5" rows={3} value={form.verification_notes ?? ""}
              onChange={(e) => setForm({ ...form, verification_notes: e.target.value || null })} />
          </label>
          <div className="sm:col-span-2">
            <button onClick={save} className="btn-primary">Save</button>
          </div>
        </div>
      )}
      {msg && <p role="status" className="font-medium text-emerald-700">{msg}</p>}
      {err && <p role="alert" className="error-text">{err}</p>}
    </section>
  );
}

function Ingestion({ token }: { token: string }) {
  const [jobs, setJobs] = useState<JobRow[]>([]);
  const [sources, setSources] = useState<SourcePage | null>(null);
  const [page, setPage] = useState(1);
  const [err, setErr] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);

  const refresh = useCallback(() => {
    setErr(null);
    Promise.all([listJobs(token), listSources(token, page)])
      .then(([j, s]) => { setJobs(j); setSources(s); })
      .catch((e) => setErr(errorMessage(e)));
  }, [token, page]);
  useEffect(refresh, [refresh]);

  const run = async () => {
    setNote(null);
    try {
      await startIngest(token, null);
      setNote("Ingestion started. Refresh in a moment to see the job.");
    } catch (e) {
      setErr(errorMessage(e));
    }
  };

  const pages = sources ? Math.max(1, Math.ceil(sources.total / sources.page_size)) : 1;
  return (
    <section className="card space-y-5 p-6">
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="mr-auto text-lg font-semibold text-ink">Ingestion and sources</h2>
        <button onClick={run} className="btn-primary !py-2">Run ingestion (all)</button>
        <button onClick={refresh} className="btn-secondary !py-2">Refresh</button>
      </div>
      {note && <p role="status" className="text-emerald-700">{note}</p>}
      {err && <ErrorBox message={err} onRetry={refresh} />}

      <div>
        <h3 className="section-title mb-2">Recent jobs</h3>
        <ul className="space-y-2 text-sm">
          {jobs.length === 0 && <li className="text-ink-mute">No jobs yet.</li>}
          {jobs.map((j) => (
            <li key={j.id} className="rounded-xl border border-slate-200 p-3">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-medium">#{j.id}</span>
                <span className={`chip ${STATUS_CHIP[j.status] ?? "border-slate-200"}`}>{j.status}</span>
                <span className="text-ink-mute">ok {j.documents_ok} · failed {j.documents_failed} · {j.started_at}</span>
              </div>
              {j.errors.length > 0 && (
                <ul className="mt-2 list-disc pl-5 text-rose-800">{j.errors.map((e) => <li key={e}>{e}</li>)}</ul>
              )}
            </li>
          ))}
        </ul>
      </div>

      <div>
        <h3 className="section-title mb-2">Sources</h3>
        <div className="overflow-x-auto rounded-xl border border-slate-200">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-ink-mute">
              <tr><th className="p-3">Scheme</th><th className="p-3">Source</th><th className="p-3">Status</th>
                <th className="p-3">Docs ok</th><th className="p-3">Failed</th></tr>
            </thead>
            <tbody>
              {sources?.items.map((r) => (
                <tr key={r.id} className="border-t border-slate-100 align-top">
                  <td className="p-3 font-medium">{r.scheme_id}</td>
                  <td className="break-all p-3">{r.url}{r.last_error && <div className="mt-1 text-rose-800">{r.last_error}</div>}</td>
                  <td className="p-3">{r.verification_status}</td>
                  <td className="p-3">{r.documents_ok}</td><td className="p-3">{r.documents_failed}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-4 flex items-center gap-4">
          <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="btn-secondary !py-1.5">Previous</button>
          <span className="text-sm text-ink-mute">Page {page} / {pages}</span>
          <button disabled={page >= pages} onClick={() => setPage(page + 1)} className="btn-secondary !py-1.5">Next</button>
        </div>
      </div>
    </section>
  );
}

export default function Admin() {
  const [token, setToken] = useState<string | null>(null);
  if (!token) return <Login onToken={setToken} />;
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <h1 className="mr-auto text-3xl font-extrabold text-ink">Administration</h1>
        <button onClick={() => setToken(null)} className="btn-secondary">Sign out</button>
      </div>
      <Ingestion token={token} />
      <SchemeEditor token={token} />
    </div>
  );
}
