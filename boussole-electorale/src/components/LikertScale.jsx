const OPTIONS = [
  { value: 1, label: "Fortement en désaccord" },
  { value: 2, label: "Plutôt en désaccord" },
  { value: 3, label: "Neutre / mitigé" },
  { value: 4, label: "Plutôt d'accord" },
  { value: 5, label: "Fortement d'accord" },
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
              className={`flex flex-col items-center gap-1.5 rounded-xl border p-2.5 text-center transition-colors sm:p-3 ${
                selected
                  ? "border-sky-500 bg-sky-500 text-white shadow-sm dark:border-sky-400 dark:bg-sky-400"
                  : "border-slate-200 bg-white text-slate-600 hover:border-sky-300 hover:bg-sky-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:border-sky-600 dark:hover:bg-slate-800"
              }`}
            >
              <span
                className={`h-3 w-3 rounded-full border-2 ${
                  selected ? "border-white bg-white" : "border-slate-300 dark:border-slate-600"
                }`}
              />
              <span className="hidden text-[11px] leading-tight sm:block">{opt.label}</span>
            </button>
          );
        })}
      </div>
      <div className="flex justify-between text-[11px] text-slate-500 dark:text-slate-400 sm:hidden">
        <span>Désaccord</span>
        <span>Accord</span>
      </div>
      <button
        type="button"
        onClick={() => onChange(null)}
        className={`self-start text-xs underline-offset-2 hover:underline ${
          value === null
            ? "font-medium text-sky-600 dark:text-sky-400"
            : "text-slate-500 dark:text-slate-400"
        }`}
      >
        Cet enjeu n'est pas important pour moi
      </button>
    </div>
  );
}
