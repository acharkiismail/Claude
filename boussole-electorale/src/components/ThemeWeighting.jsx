const LEVELS = [
  { value: 1, label: "Peu important" },
  { value: 2, label: "Important" },
  { value: 3, label: "Très important" },
];

export default function ThemeWeighting({ themes, weights, onChange, onContinue, onSkip }) {
  return (
    <div className="mx-auto max-w-2xl px-4 py-8 sm:py-12 sm:px-6">
      <h1 className="font-display text-2xl font-semibold tracking-tight sm:text-3xl">
        Quelle importance accordez-vous à chaque enjeu ?
      </h1>
      <p className="mt-3 text-sm leading-relaxed text-[var(--ink-secondary)]">
        Cette pondération influence votre résultat final : les enjeux jugés plus importants
        comptent davantage dans le calcul d'affinité. Vous pouvez aussi passer cette étape et
        garder tous les enjeux à poids égal.
      </p>

      <div className="mt-7 space-y-2.5">
        {themes.map((theme) => (
          <div
            key={theme.id}
            className="flex flex-col gap-3 rounded-xl border border-[var(--hairline)] bg-[var(--surface)] p-4 sm:flex-row sm:items-center sm:justify-between"
          >
            <span className="text-sm font-medium text-[var(--ink)]">{theme.name}</span>
            <div className="grid grid-cols-3 gap-1.5">
              {LEVELS.map((level) => {
                const selected = (weights[theme.id] ?? 1) === level.value;
                return (
                  <button
                    key={level.value}
                    type="button"
                    onClick={() => onChange(theme.id, level.value)}
                    className="rounded-lg border px-2.5 py-1.5 text-xs font-medium transition-colors"
                    style={
                      selected
                        ? { backgroundColor: "var(--accent)", borderColor: "var(--accent)", color: "var(--on-accent)" }
                        : { borderColor: "var(--hairline)", color: "var(--ink-secondary)" }
                    }
                  >
                    {level.label}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 flex flex-col-reverse gap-3 sm:flex-row sm:justify-between">
        <button
          type="button"
          onClick={onSkip}
          className="text-sm font-medium text-[var(--ink-secondary)] underline-offset-2 hover:underline"
        >
          Passer cette étape (poids égal)
        </button>
        <button
          type="button"
          onClick={onContinue}
          className="rounded-xl px-6 py-3 text-sm font-semibold shadow-sm"
          style={{ backgroundColor: "var(--accent)", color: "var(--on-accent)" }}
        >
          Continuer vers le questionnaire →
        </button>
      </div>
    </div>
  );
}
