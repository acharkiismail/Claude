import { partyColor } from "../lib/colors";

export default function RankingChart({ rankedParties }) {
  return (
    <div className="space-y-3">
      {rankedParties.map(({ party, affinity }, i) => (
        <div key={party.id} className="flex items-center gap-3">
          <span className="w-4 shrink-0 text-right text-sm font-semibold text-[var(--ink-muted)]">
            {i + 1}
          </span>
          <span
            className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-[10px] font-bold text-white"
            style={{ backgroundColor: partyColor(party) }}
          >
            {party.shortName.slice(0, 2)}
          </span>
          <div className="w-14 shrink-0 text-sm font-semibold text-[var(--ink)]">
            {party.shortName}
          </div>
          <div className="h-8 flex-1 overflow-hidden rounded-lg" style={{ backgroundColor: "var(--hairline)" }}>
            <div
              className="flex h-full items-center justify-end rounded-lg px-2 text-xs font-semibold text-white transition-all duration-500"
              style={{ width: `${Math.max(affinity, 8)}%`, backgroundColor: partyColor(party) }}
            >
              {affinity.toFixed(1)}%
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
