const OPTIONS = [
  { value: 1, label: "Fortement en désaccord", short: "--", bg: "var(--disagree-strong)", fg: "#ffffff" },
  { value: 2, label: "Plutôt en désaccord", short: "-", bg: "var(--disagree)", fg: "#3f0d18" },
  { value: 3, label: "Neutre / mitigé", short: "=", bg: "var(--neutral-likert)", fg: "var(--ink-secondary)" },
  { value: 4, label: "Plutôt d'accord", short: "+", bg: "var(--agree)", fg: "#04312c" },
  { value: 5, label: "Fortement d'accord", short: "++", bg: "var(--agree-strong)", fg: "#ffffff" },
];

export default function LikertScale({ value, onChange }) {
  return (
    <div className="flex flex-col gap-2">
      <div className="grid grid-cols-5 gap-1.5 sm:gap-2">
        {OPTIONS.map((opt) => {
          const selected = value === opt.value;
          return (
            <button
              key={opt.value}
              type="button"
              onClick={() => onChange(opt.value)}
              aria-pressed={selected}
              aria-label={opt.label}
              className="flex flex-col items-center gap-1.5 rounded-xl border p-2.5 text-center transition-all sm:p-3"
              style={{
                borderColor: selected ? opt.bg : "var(--hairline)",
                backgroundColor: selected ? opt.bg : "var(--surface)",
                color: selected ? opt.fg : "var(--ink-secondary)",
                transform: selected ? "translateY(-1px)" : undefined,
                boxShadow: selected ? "0 2px 8px rgba(0,0,0,0.12)" : undefined,
              }}
            >
              <span className="text-sm font-bold leading-none sm:hidden">{opt.short}</span>
              <span
                className="hidden h-2.5 w-2.5 rounded-full border-2 sm:block"
                style={{ borderColor: selected ? opt.fg : "var(--hairline)" }}
              />
              <span className="hidden text-[11px] leading-tight sm:block">{opt.label}</span>
            </button>
          );
        })}
      </div>
      <div className="flex justify-between text-[11px] text-[var(--ink-muted)] sm:hidden">
        <span>Désaccord</span>
        <span>Accord</span>
      </div>
      <button
        type="button"
        onClick={() => onChange(null)}
        className="self-start text-xs underline-offset-2 hover:underline"
        style={{
          color: value === null ? "var(--accent-strong)" : "var(--ink-muted)",
          fontWeight: value === null ? 600 : 400,
        }}
      >
        Cet enjeu n'est pas important pour moi
      </button>
    </div>
  );
}
