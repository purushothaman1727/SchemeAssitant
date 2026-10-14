export default function Skeleton({ rows = 3 }: { rows?: number }) {
  return (
    <div aria-hidden="true" className="space-y-4">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="card shimmer border-l-4 border-l-slate-200 p-6">
          <div className="mb-4 flex gap-2">
            <div className="h-5 w-28 rounded-full bg-slate-200" />
            <div className="h-5 w-20 rounded-full bg-slate-200" />
          </div>
          <div className="mb-3 h-5 w-2/3 rounded-lg bg-slate-200" />
          <div className="mb-2 h-3 w-full rounded bg-slate-100" />
          <div className="h-3 w-4/5 rounded bg-slate-100" />
        </div>
      ))}
    </div>
  );
}
