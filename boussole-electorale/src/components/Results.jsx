import { useState } from "react";
import RankingChart from "./RankingChart";
import CompassChart from "./CompassChart";
import RadarChart from "./RadarChart";
import MatchHighlights from "./MatchHighlights";
import ReliabilityBadge from "./ReliabilityBadge";
import { partyColor } from "../lib/colors";
import { computeMatchHighlights } from "../lib/scoring";

const LIKERT_LABEL = {
  1: "Fortement en désaccord",
  2: "Plutôt en désaccord",
  3: "Neutre / mitigé",
  4: "Plutôt d'accord",
  5: "Fortement d'accord",
};

function Card({ title, subtitle, children }) {
  return (
    <section className="mt-6 rounded-2xl border border-[var(--hairline)] bg-[var(--surface)] p-5 shadow-[0_1px_2px_rgba(0,0,0,0.04)]">
      <h2 className="text-sm font-semibold text-[var(--ink)]">{title}</h2>
      {subtitle && <p className="mt-1 text-xs text-[var(--ink-muted)]">{subtitle}</p>}
      <div className="mt-4">{children}</div>
    </section>
  );
}

export default function Results({
  statements,
  themes,
  parties,
  partiesById,
  answers,
  rankedAffinities,
  userPosition,
  partyPositions,
  themeAxes,
  userThemeScores,
  partyThemeScores,
  onRestart,
}) {
  const [openTheme, setOpenTheme] = useState(null);

  const rankedParties = rankedAffinities.map((r) => ({
    party: partiesById[r.partyId],
    affinity: r.affinity,
  }));
  const top = rankedParties[0];
  const topHighlights = computeMatchHighlights(statements, answers, top.party.id);
  const userRadarValues = themeAxes.map((axis) => userThemeScores[axis.id] ?? 50);

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6 sm:py-12">
      <p className="text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
        Vos résultats
      </p>
      <h1 className="font-display mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
        Vous êtes le plus proche {top.party.article}{" "}
        <span style={{ color: partyColor(top.party) }}>{top.party.name}</span>
      </h1>
      <p className="mt-2 text-sm text-[var(--ink-secondary)]">
        {top.affinity.toFixed(1)}% d'affinité sur les enjeux et la pondération que vous avez
        choisis — dirigé par {top.party.leader}.
      </p>

      <Card title="Classement d'affinité">
        <RankingChart rankedParties={rankedParties} />
      </Card>

      <Card
        title={`Pourquoi ${top.party.shortName} ?`}
        subtitle="Les énoncés qui expliquent le plus votre résultat, plutôt qu'un simple pourcentage."
      >
        <MatchHighlights party={top.party} highlights={topHighlights} />
      </Card>

      <Card
        title="Votre profil par enjeu"
        subtitle="Un score de 0 à 100 par thème (façon smartspider) : plus le point s'éloigne du centre, plus vous êtes en accord avec les énoncés de ce thème."
      >
        <RadarChart axes={themeAxes} userValues={userRadarValues} />
      </Card>

      <Card
        title="Comparaison thème par thème"
        subtitle="Votre profil (contour pointillé) superposé à celui de chaque parti (aplat coloré)."
      >
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {parties.map((party) => {
            const partyRadarValues = themeAxes.map((axis) => partyThemeScores[party.id][axis.id] ?? 50);
            return (
              <div
                key={party.id}
                className="rounded-xl border p-3 text-center"
                style={{ borderColor: "var(--hairline)" }}
              >
                <p className="text-xs font-semibold" style={{ color: partyColor(party) }}>
                  {party.shortName}
                </p>
                <RadarChart axes={themeAxes} userValues={userRadarValues} party={party} partyValues={partyRadarValues} size="small" />
              </div>
            );
          })}
        </div>
      </Card>

      <Card
        title="Positionnement sur deux axes"
        subtitle="Vue simplifiée : économique (gauche-droite) et identité nationale (fédéraliste-souverainiste)."
      >
        <CompassChart userPosition={userPosition} partyPositions={partyPositions} />
      </Card>

      <Card
        title="Détail par enjeu et sources"
        subtitle="Comparez votre réponse à chaque énoncé avec la position documentée de chaque parti."
      >
        <div className="divide-y" style={{ borderColor: "var(--hairline)" }}>
          {themes.map((theme) => {
            const themeStatements = statements.filter((s) => s.themeId === theme.id);
            const isOpen = openTheme === theme.id;
            return (
              <div key={theme.id} className="py-3" style={{ borderColor: "var(--hairline)" }}>
                <button
                  type="button"
                  onClick={() => setOpenTheme(isOpen ? null : theme.id)}
                  className="flex w-full items-center justify-between text-left text-sm font-medium text-[var(--ink)]"
                >
                  {theme.name}
                  <span className="text-[var(--ink-muted)]">{isOpen ? "−" : "+"}</span>
                </button>
                {isOpen && (
                  <div className="mt-3 space-y-5">
                    {themeStatements.map((statement) => (
                      <div key={statement.id} className="rounded-xl p-4" style={{ backgroundColor: "var(--page)" }}>
                        <p className="text-sm font-medium text-[var(--ink)]">{statement.text}</p>
                        {statement.context && (
                          <p className="mt-1 text-xs italic text-[var(--ink-muted)]">{statement.context}</p>
                        )}
                        <p className="mt-2 text-xs text-[var(--ink-muted)]">
                          Votre réponse :{" "}
                          <span className="font-semibold text-[var(--ink-secondary)]">
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
                                <span className="mb-0.5 flex flex-wrap items-center gap-1.5">
                                  <span
                                    className="inline-block h-2 w-2 rounded-full"
                                    style={{ backgroundColor: partyColor(party) }}
                                  />
                                  <span className="font-semibold text-[var(--ink-secondary)]">
                                    {party.shortName} ({LIKERT_LABEL[pos.value]})
                                  </span>
                                  <ReliabilityBadge reliability={pos.reliability} />
                                </span>
                                <span className="text-[var(--ink-muted)]">{pos.source}</span>
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
      </Card>

      <button
        type="button"
        onClick={onRestart}
        className="mt-8 rounded-xl border px-5 py-2.5 text-sm font-medium text-[var(--ink-secondary)]"
        style={{ borderColor: "var(--hairline)" }}
      >
        ↺ Recommencer le test
      </button>
    </div>
  );
}
