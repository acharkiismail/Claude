const LIKERT_SHORT = {
  1: "Fortement en désaccord",
  2: "Plutôt en désaccord",
  3: "Neutre",
  4: "Plutôt d'accord",
  5: "Fortement d'accord",
};

function StatementRow({ item, party }) {
  return (
    <li className="rounded-xl bg-[var(--page)] p-3.5">
      <p className="text-sm font-medium text-[var(--ink)]">{item.statement.text}</p>
      <p className="mt-1.5 text-xs text-[var(--ink-secondary)]">
        Vous : <span className="font-semibold">{LIKERT_SHORT[item.userValue]}</span>
        <span className="mx-1.5 text-[var(--ink-muted)]">·</span>
        {party.shortName} :{" "}
        <span className="font-semibold" style={{ color: `var(${party.colorVar})` }}>
          {LIKERT_SHORT[item.partyValue]}
        </span>
      </p>
    </li>
  );
}

export default function MatchHighlights({ party, highlights }) {
  const { agreements, disagreements } = highlights;

  return (
    <div className="grid gap-5 sm:grid-cols-2">
      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wide text-[var(--status-good)]">
          Où vous convergez le plus
        </h3>
        <ul className="mt-3 space-y-2">
          {agreements.map((item) => (
            <StatementRow key={item.statement.id} item={item} party={party} />
          ))}
        </ul>
      </div>
      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wide text-[var(--disagree-strong)]">
          Où vous divergez le plus
        </h3>
        {disagreements.length > 0 ? (
          <ul className="mt-3 space-y-2">
            {disagreements.map((item) => (
              <StatementRow key={item.statement.id} item={item} party={party} />
            ))}
          </ul>
        ) : (
          <p className="mt-3 text-sm text-[var(--ink-secondary)]">
            Aucun désaccord marqué — vos réponses rejoignent {party.shortName} sur la plupart des énoncés.
          </p>
        )}
      </div>
    </div>
  );
}
