import CompassMark from "./CompassMark";

export default function Header({ stepIndex, stepCount }) {
  return (
    <header className="border-b border-[var(--hairline)] bg-[var(--surface)]/80 backdrop-blur">
      <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-3 sm:px-6">
        <div className="flex items-center gap-2">
          <CompassMark />
          <span className="font-display text-[15px] font-semibold tracking-tight text-[var(--ink)]">
            Boussole <span style={{ color: "var(--accent)" }}>2026</span>
          </span>
        </div>
        {stepIndex != null && (
          <div className="flex items-center gap-1.5">
            {Array.from({ length: stepCount }).map((_, i) => (
              <span
                key={i}
                className="h-1.5 w-5 rounded-full transition-colors"
                style={{
                  backgroundColor: i <= stepIndex ? "var(--accent)" : "var(--hairline)",
                }}
              />
            ))}
          </div>
        )}
      </div>
    </header>
  );
}
