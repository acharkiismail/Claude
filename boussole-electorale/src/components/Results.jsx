import { useState } from "react";
import RankingChart from "./RankingChart";
import CompassChart from "./CompassChart";

const LIKERT_LABEL = {
  1: "Fortement en désaccord",
  2: "Plutôt en désaccord",
  3: "Neutre / mitigé",
  4: "Plutôt d'accord",
  5: "Fortement d'accord",
};

export default function Results({
  statements,
  themes,
  parties,
  partiesById,
  answers,
  rankedAffinities,
  userPosition,
  partyPositions,
  onRestart,
}) {
  const [openTheme, setOpenTheme] = useState(null);

  const rankedParties = rankedAffinities.map((r) => ({
    party: partiesById[r.partyId],
    affinity: r.affinity,
  }));
  const top = rankedParties[0];

  return (
    <div className="mx-auto max-w-3xl px-4 py-10 sm:py-14">
      <p className="text-sm font-medium uppercase tracking-wide text-sky-600 dark:text-sky-400">
        Vos résultats
      </p>
      <h1 className="mt-2 text-2xl font-bold tracking-tight sm:text-3xl">
        Vous êtes le plus proche de{" "}
        <span style={{ color: top.party.color }}>{top.party.name}</span>
      </h1>
      <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
        {top.affinity.toFixed(1)}% d'affinité sur les enjeux et la pondération que vous avez
        choisis.
      </p>

      <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
        <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
          Classement d'affinité
        </h2>
        <div className="mt-4">
          <RankingChart rankedParties={rankedParties} />
        </div>
      </section>

      <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
        <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
          Positionnement sur deux axes
        </h2>
        <div className="mt-4">
          <CompassChart userPosition={userPosition} partyPositions={partyPositions} />
        </div>
      </section>

      <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
        <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
          Détail par enjeu et sources
        </h2>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          Comparez votre réponse à chaque énoncé avec la position documentée de chaque parti.
        </p>
        <div className="mt-4 divide-y divide-slate-200 dark:divide-slate-800">
          {themes.map((theme) => {
            const themeStatements = statements.filter((s) => s.themeId === theme.id);
            const isOpen = openTheme === theme.id;
            return (
              <div key={theme.id} className="py-3">
                <button
                  type="button"
                  onClick={() => setOpenTheme(isOpen ? null : theme.id)}
                  className="flex w-full items-center justify-between text-left text-sm font-medium text-slate-900 dark:text-slate-100"
                >
                  {theme.name}
                  <span className="text-slate-400">{isOpen ? "−" : "+"}</span>
                </button>
                {isOpen && (
                  <div className="mt-3 space-y-5">
                    {themeStatements.map((statement) => (
                      <div key={statement.id} className="rounded-xl bg-slate-50 p-4 dark:bg-slate-800/60">
                        <p className="text-sm font-medium text-slate-800 dark:text-slate-100">
                          {statement.text}
                        </p>
                        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                          Votre réponse :{" "}
                          <span className="font-semibold text-slate-700 dark:text-slate-200">
                            {answers[statement.id] != null
                              ? LIKERT_LABEL[answers[statement.id]]
                              : "Pas important pour vous"}
                          </span>
                        </p>
                        <ul className="mt-3 space-y-2">
                          {parties.map((party) => {
                            const pos = statement.positions[party.id];
                            if (!pos) return null;
                            return (
                              <li key={party.id} className="text-xs leading-relaxed">
                                <span
                                  className="mr-1.5 inline-block h-2 w-2 rounded-full align-middle"
                                  style={{ backgroundColor: party.color }}
                                />
                                <span className="font-semibold text-slate-700 dark:text-slate-200">
                                  {party.shortName} ({LIKERT_LABEL[pos.value]}) —
                                </span>{" "}
                                <span className="text-slate-500 dark:text-slate-400">{pos.source}</span>
                              </li>
                            );
                          })}
                        </ul>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </section>

      <button
        type="button"
        onClick={onRestart}
        className="mt-8 rounded-xl border border-slate-300 px-5 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
      >
        ↺ Recommencer le test
      </button>
    </div>
  );
}
