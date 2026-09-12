const LEVELS = [
  { value: 1, label: "Peu important" },
  { value: 2, label: "Important" },
  { value: 3, label: "Très important" },
];

export default function ThemeWeighting({ themes, weights, onChange, onContinue, onSkip }) {
  return (
    <div className="mx-auto max-w-2xl px-4 py-10 sm:py-14">
      <p className="text-sm font-medium uppercase tracking-wide text-sky-600 dark:text-sky-400">
        Étape 1 sur 2
      </p>
      <h1 className="mt-2 text-2xl font-bold tracking-tight sm:text-3xl">
        Quelle importance accordez-vous à chaque enjeu ?
      </h1>
      <p className="mt-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
        Cette pondération influencera votre résultat final : les enjeux jugés plus importants
        auront plus de poids dans le calcul d'affinité. Vous pouvez aussi passer cette étape et
        garder tous les enjeux à poids égal.
      </p>

      <div className="mt-8 space-y-3">
        {themes.map((theme) => (
          <div
            key={theme.id}
            className="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-4 sm:flex-row sm:items-center sm:justify-between dark:border-slate-800 dark:bg-slate-900"
          >
            <span className="text-sm font-medium text-slate-900 dark:text-slate-100">
              {theme.name}
            </span>
            <div className="grid grid-cols-3 gap-1.5">
              {LEVELS.map((level) => {
                const selected = (weights[theme.id] ?? 1) === level.value;
                return (
                  <button
                    key={level.value}
                    type="button"
                    onClick={() => onChange(theme.id, level.value)}
                    className={`rounded-lg border px-2.5 py-1.5 text-xs font-medium transition-colors ${
                      selected
                        ? "border-sky-500 bg-sky-500 text-white"
                        : "border-slate-200 bg-white text-slate-600 hover:border-sky-300 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
                    }`}
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
          className="text-sm font-medium text-slate-500 underline-offset-2 hover:underline dark:text-slate-400"
        >
          Passer cette étape (poids égal)
        </button>
        <button
          type="button"
          onClick={onContinue}
          className="rounded-xl bg-sky-600 px-6 py-3 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-sky-700"
        >
          Continuer vers le questionnaire →
        </button>
      </div>
    </div>
  );
}
