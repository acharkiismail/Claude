import LikertScale from "./LikertScale";

export default function Questionnaire({
  statements,
  themesById,
  answers,
  currentIndex,
  onAnswer,
  onNext,
  onBack,
  onFinish,
}) {
  const statement = statements[currentIndex];
  const theme = themesById[statement.themeId];
  const isLast = currentIndex === statements.length - 1;
  const hasAnswer = Object.prototype.hasOwnProperty.call(answers, statement.id);
  const progress = ((currentIndex + 1) / statements.length) * 100;

  return (
    <div className="mx-auto flex min-h-[calc(100dvh-2rem)] max-w-2xl flex-col px-4 py-8 sm:py-12">
      <div>
        <div className="flex items-center justify-between text-xs font-medium text-slate-500 dark:text-slate-400">
          <span>
            Énoncé {currentIndex + 1} / {statements.length}
          </span>
          <span className="text-sky-600 dark:text-sky-400">{theme.shortName}</span>
        </div>
        <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
          <div
            className="h-full rounded-full bg-sky-500 transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <div className="flex flex-1 flex-col justify-center py-10">
        <p className="text-xl font-semibold leading-snug text-slate-900 sm:text-2xl dark:text-slate-50">
          {statement.text}
        </p>

        <div className="mt-8">
          <LikertScale
            value={answers[statement.id] ?? null}
            onChange={(value) => onAnswer(statement.id, value)}
          />
        </div>
      </div>

      <div className="flex items-center justify-between gap-3 border-t border-slate-200 pt-5 dark:border-slate-800">
        <button
          type="button"
          onClick={onBack}
          disabled={currentIndex === 0}
          className="rounded-xl px-4 py-2.5 text-sm font-medium text-slate-600 disabled:opacity-0 dark:text-slate-300"
        >
          ← Précédent
        </button>
        {isLast ? (
          <button
            type="button"
            onClick={onFinish}
            disabled={!hasAnswer}
            className="rounded-xl bg-sky-600 px-6 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-sky-700 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Voir mes résultats →
          </button>
        ) : (
          <button
            type="button"
            onClick={onNext}
            disabled={!hasAnswer}
            className="rounded-xl bg-sky-600 px-6 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-sky-700 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Suivant →
          </button>
        )}
      </div>
    </div>
  );
}
