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
    <div className="mx-auto flex min-h-[calc(100dvh-3.5rem)] max-w-2xl flex-col px-4 py-6 sm:px-6 sm:py-10">
      <div>
        <div className="flex items-center justify-between text-xs font-medium text-[var(--ink-muted)]">
          <span>
            Énoncé {currentIndex + 1} / {statements.length}
          </span>
          <span className="font-semibold" style={{ color: "var(--accent-strong)" }}>
            {theme.shortName}
          </span>
        </div>
        <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full" style={{ backgroundColor: "var(--hairline)" }}>
          <div
            className="h-full rounded-full transition-all duration-300"
            style={{ width: `${progress}%`, backgroundColor: "var(--accent)" }}
          />
        </div>
      </div>

      <div className="flex flex-1 flex-col justify-center py-8 sm:py-10">
        <p className="font-display text-xl font-semibold leading-snug sm:text-2xl">
          {statement.text}
        </p>
        {statement.context && (
          <p className="mt-3 border-l-2 pl-3 text-sm leading-relaxed text-[var(--ink-secondary)]" style={{ borderColor: "var(--hairline)" }}>
            {statement.context}
          </p>
        )}

        <div className="mt-8">
          <LikertScale
            value={answers[statement.id] ?? null}
            onChange={(value) => onAnswer(statement.id, value)}
          />
        </div>
      </div>

      <div className="flex items-center justify-between gap-3 border-t pt-5" style={{ borderColor: "var(--hairline)" }}>
        <button
          type="button"
          onClick={onBack}
          disabled={currentIndex === 0}
          className="rounded-xl px-4 py-2.5 text-sm font-medium text-[var(--ink-secondary)] disabled:opacity-0"
        >
          ← Précédent
        </button>
        {isLast ? (
          <button
            type="button"
            onClick={onFinish}
            disabled={!hasAnswer}
            className="rounded-xl px-6 py-2.5 text-sm font-semibold shadow-sm disabled:cursor-not-allowed disabled:opacity-40"
            style={{ backgroundColor: "var(--accent)", color: "var(--on-accent)" }}
          >
            Voir mes résultats →
          </button>
        ) : (
          <button
            type="button"
            onClick={onNext}
            disabled={!hasAnswer}
            className="rounded-xl px-6 py-2.5 text-sm font-semibold shadow-sm disabled:cursor-not-allowed disabled:opacity-40"
            style={{ backgroundColor: "var(--accent)", color: "var(--on-accent)" }}
          >
            Suivant →
          </button>
        )}
      </div>
    </div>
  );
}
