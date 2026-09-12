export default function RankingChart({ rankedParties }) {
  return (
    <div className="space-y-3">
      {rankedParties.map(({ party, affinity }, i) => (
        <div key={party.id} className="flex items-center gap-3">
          <span className="w-5 shrink-0 text-right text-sm font-semibold text-slate-400 dark:text-slate-500">
            {i + 1}
          </span>
          <div className="w-16 shrink-0 text-sm font-semibold text-slate-900 dark:text-slate-100">
            {party.shortName}
          </div>
          <div className="h-8 flex-1 overflow-hidden rounded-lg bg-slate-100 dark:bg-slate-800">
            <div
              className="flex h-full items-center justify-end rounded-lg px-2 text-xs font-semibold text-white transition-all duration-500"
              style={{
                width: `${Math.max(affinity, 6)}%`,
                backgroundColor: party.color,
              }}
            >
              {affinity.toFixed(1)}%
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
