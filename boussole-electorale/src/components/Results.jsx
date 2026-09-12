import { useMemo, useState } from "react";
import RankingChart from "./RankingChart";
import CompassChart from "./CompassChart";
import RadarChart from "./RadarChart";
import MatchHighlights from "./MatchHighlights";
import ReliabilityBadge from "./ReliabilityBadge";
import meta from "../data/meta.json";
import { partyColor } from "../lib/colors";
import {
  activeThemes,
  computeAffinities,
  computeAxisPosition,
  computeCompleteness,
  computeMatchHighlights,
  computeThemeAffinities,
  isConsensus,
  partyAnswersFromPositions,
  themeExtremes,
} from "../lib/scoring";
import ShareSection from "./ShareSection";
import { encodeResult, resultUrl } from "../lib/shareLink";

const LIKERT_LABEL = {
  1: "Fortement en désaccord",
  2: "Plutôt en désaccord",
  3: "Neutre / mitigé",
  4: "Plutôt d'accord",
  5: "Fortement d'accord",
};

// En deçà de cet écart, la différence entre deux partis relève du bruit de mesure
// et l'app le dit plutôt que de trancher.
const TIE_THRESHOLD = 2;

function Card({ title, subtitle, children }) {
  return (
    <section className="mt-6 rounded-2xl border border-[var(--hairline)] bg-[var(--surface)] p-5 shadow-[0_1px_2px_rgba(0,0,0,0.04)]">
      <h2 className="text-sm font-semibold text-[var(--ink)]">{title}</h2>
      {subtitle && <p className="mt-1 text-xs leading-relaxed text-[var(--ink-muted)]">{subtitle}</p>}
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
  weights,
  mode = "full",
  viewingSharedResult = false,
  onRestart,
  onContinueFull,
}) {
  const [openTheme, setOpenTheme] = useState(null);

  const model = useMemo(() => {
    const ranked = computeAffinities(statements, parties, answers, weights)
      .filter((r) => r.affinity != null)
      .map((r) => ({ ...r, party: partiesById[r.partyId] }));
    const radarThemes = activeThemes(statements, themes, answers);
    const themeAffinities = Object.fromEntries(
      parties.map((p) => [p.id, computeThemeAffinities(statements, themes, answers, p.id)])
    );
    return {
      ranked,
      radarThemes,
      themeAffinities,
      userPosition: computeAxisPosition(statements, answers),
      partyPositions: parties.map((party) => ({
        party,
        position: computeAxisPosition(statements, partyAnswersFromPositions(statements, party.id)),
      })),
      answeredCount: statements.filter((s) => answers[s.id] != null).length,
    };
  }, [statements, themes, parties, partiesById, answers, weights]);

  const { ranked, radarThemes, themeAffinities, answeredCount } = model;

  if (ranked.length === 0) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 sm:px-6">
        <h1 className="font-display text-2xl font-semibold tracking-tight sm:text-3xl">
          Aucune affinité calculable
        </h1>
        <p className="mt-3 text-sm leading-relaxed text-[var(--ink-secondary)]">
          Vous avez marqué tous les énoncés comme « pas important pour moi », il n'y a donc rien à
          comparer aux positions des partis. Reprenez le questionnaire en répondant à au moins
          quelques énoncés.
        </p>
        <button
          type="button"
          onClick={onRestart}
          className="mt-6 rounded-xl px-5 py-2.5 text-sm font-semibold shadow-sm"
          style={{ backgroundColor: "var(--accent)", color: "var(--on-accent)" }}
        >
          ↺ Recommencer
        </button>
      </div>
    );
  }

  const top = ranked[0];
  const runnerUp = ranked[1];
  const isTie = runnerUp && top.affinity - runnerUp.affinity < TIE_THRESHOLD;
  const topHighlights = computeMatchHighlights(statements, answers, top.party.id);

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6 sm:py-12">
      {viewingSharedResult && (
        <div
          className="mb-6 flex flex-col gap-3 rounded-2xl border p-4 sm:flex-row sm:items-center sm:justify-between"
          style={{ borderColor: "var(--accent)", backgroundColor: "var(--accent-soft)" }}
        >
          <p className="text-sm font-medium text-[var(--ink)]">
            Vous regardez le résultat de quelqu'un d'autre.
          </p>
          <button
            type="button"
            onClick={onRestart}
            className="shrink-0 rounded-xl px-4 py-2 text-sm font-semibold"
            style={{ backgroundColor: "var(--accent)", color: "var(--on-accent)" }}
          >
            Faire le mien →
          </button>
        </div>
      )}

      <p className="text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
        {viewingSharedResult ? "Résultat partagé" : "Vos résultats"}
      </p>

      {isTie ? (
        <>
          <h1 className="font-display mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
            Résultat serré entre{" "}
            <span style={{ color: partyColor(top.party) }}>{top.party.shortName}</span> et{" "}
            <span style={{ color: partyColor(runnerUp.party) }}>{runnerUp.party.shortName}</span>
          </h1>
          <p className="mt-2 text-sm leading-relaxed text-[var(--ink-secondary)]">
            {top.party.name} ({top.affinity.toFixed(1)} %) devance {runnerUp.party.name} (
            {runnerUp.affinity.toFixed(1)} %) de moins de {TIE_THRESHOLD} points — un écart trop
            faible pour être significatif. Traitez-les comme équivalents et regardez plutôt les
            enjeux ci-dessous, où ils se distinguent vraiment.
          </p>
        </>
      ) : (
        <>
          <h1 className="font-display mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
            Vous êtes le plus proche {top.party.article}{" "}
            <span style={{ color: partyColor(top.party) }}>{top.party.name}</span>
          </h1>
          <p className="mt-2 text-sm text-[var(--ink-secondary)]">
            {top.affinity.toFixed(1)} % d'affinité sur les enjeux et la pondération que vous avez
            choisis — dirigé par {top.party.leader}.
          </p>
        </>
      )}

      {mode === "short" && !viewingSharedResult && (
        <div
          className="mt-6 flex flex-col gap-3 rounded-2xl border p-4 sm:flex-row sm:items-center sm:justify-between"
          style={{ borderColor: "var(--hairline)", backgroundColor: "var(--surface)" }}
        >
          <p className="text-sm text-[var(--ink-secondary)]">
            Ce résultat repose sur {answeredCount} énoncés. Le questionnaire complet en compte{" "}
            {statements.length} et affine nettement le portrait.
          </p>
          <button
            type="button"
            onClick={onContinueFull}
            className="shrink-0 rounded-xl px-4 py-2 text-sm font-semibold"
            style={{ backgroundColor: "var(--accent)", color: "var(--on-accent)" }}
          >
            Continuer →
          </button>
        </div>
      )}

      <Card
        title="Partager votre résultat"
        subtitle="Une image carrée prête à publier, ou un lien qui reproduit exactement ce résultat."
      >
        <ShareSection
          cardData={{
            topParty: top.party,
            affinity: top.affinity,
            isTie,
            runnerUp: runnerUp?.party,
            ranked: ranked.map((r) => ({ party: r.party, affinity: r.affinity })),
            radarValues: radarThemes.map((t) => themeAffinities[top.party.id][t.id] ?? 0),
            ...themeExtremes(themeAffinities[top.party.id], radarThemes),
          }}
          shareUrl={resultUrl(encodeResult(statements, themes, answers, weights))}
        />
      </Card>

      <Card
        title="Classement d'affinité"
        subtitle={`Calculé sur les ${answeredCount} énoncés auxquels vous avez répondu. Un écart de moins de ${TIE_THRESHOLD} points entre deux partis n'est pas significatif.`}
      >
        <RankingChart
          rankedParties={ranked}
          tieThreshold={TIE_THRESHOLD}
          completeness={Object.fromEntries(
            parties.map((p) => [p.id, computeCompleteness(statements, p.id)])
          )}
        />
      </Card>

      <Card
        title={`Pourquoi ${top.party.shortName} ?`}
        subtitle="Les énoncés qui expliquent le plus votre résultat, plutôt qu'un simple pourcentage."
      >
        <MatchHighlights party={top.party} highlights={topHighlights} />
      </Card>

      {radarThemes.length >= 3 ? (
        <Card
          title="Affinité par enjeu"
          subtitle="Votre affinité de 0 à 100 avec chaque parti, thème par thème. 100 = vos réponses coïncident sur tous les énoncés du thème. Un parti peut vous rejoindre sur la santé et vous opposer sur l'identité."
        >
          <p className="mb-1 text-center text-xs font-semibold" style={{ color: partyColor(top.party) }}>
            {top.party.name}
          </p>
          <RadarChart
            axes={radarThemes}
            values={radarThemes.map((t) => themeAffinities[top.party.id][t.id] ?? 0)}
            color={partyColor(top.party)}
            label={`Votre affinité par enjeu avec ${top.party.name}`}
          />
          <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
            {ranked.slice(1).map(({ party, affinity }) => (
              <div
                key={party.id}
                className="rounded-xl border p-2 text-center"
                style={{ borderColor: "var(--hairline)" }}
              >
                <p className="text-xs font-semibold" style={{ color: partyColor(party) }}>
                  {party.shortName}
                </p>
                <p className="text-[10px] text-[var(--ink-muted)]">{affinity.toFixed(0)} %</p>
                <RadarChart
                  axes={radarThemes}
                  values={radarThemes.map((t) => themeAffinities[party.id][t.id] ?? 0)}
                  color={partyColor(party)}
                  label={`Votre affinité par enjeu avec ${party.name}`}
                  size="small"
                />
              </div>
            ))}
          </div>
        </Card>
      ) : (
        <Card title="Affinité par enjeu">
          <p className="text-sm text-[var(--ink-secondary)]">
            Trop peu de thèmes évalués pour tracer un profil — répondez à des énoncés dans au moins
            trois thèmes différents.
          </p>
        </Card>
      )}

      <Card
        title="Positionnement sur deux axes"
        subtitle="Vue simplifiée : économique (gauche-droite) et identité nationale (fédéraliste-souverainiste)."
      >
        <CompassChart userPosition={model.userPosition} partyPositions={model.partyPositions} />
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
                  aria-expanded={isOpen}
                  className="flex w-full items-center justify-between text-left text-sm font-medium text-[var(--ink)]"
                >
                  {theme.name}
                  <span className="text-[var(--ink-muted)]">{isOpen ? "−" : "+"}</span>
                </button>
                {isOpen && (
                  <div className="mt-3 space-y-5">
                    {themeStatements.map((statement) => (
                      <div
                        key={statement.id}
                        className="rounded-xl p-4"
                        style={{ backgroundColor: "var(--page)" }}
                      >
                        <p className="text-sm font-medium text-[var(--ink)]">{statement.text}</p>
                        {statement.context && (
                          <p className="mt-1 text-xs italic text-[var(--ink-muted)]">
                            {statement.context}
                          </p>
                        )}
                        {isConsensus(statement) && (
                          <p className="mt-2 text-xs font-medium" style={{ color: "var(--accent)" }}>
                            Consensus : tous les partis tiennent essentiellement la même position
                            sur cet énoncé, il ne les départage donc pas.
                          </p>
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
                            const unknown = pos.reliability === "unknown";
                            return (
                              <li key={party.id} className="text-xs leading-relaxed">
                                <span className="mb-0.5 flex flex-wrap items-center gap-1.5">
                                  <span
                                    className="inline-block h-2 w-2 rounded-full"
                                    style={{ backgroundColor: partyColor(party) }}
                                  />
                                  <span className="font-semibold text-[var(--ink-secondary)]">
                                    {party.shortName}
                                    {unknown ? "" : ` (${LIKERT_LABEL[pos.value]})`}
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

      <p className="mt-6 text-xs leading-relaxed text-[var(--ink-muted)]">
        Positions des partis relevées le {meta.dataDateLabel}, pour l'élection du{" "}
        {meta.electionDateLabel}. Un résultat n'est pas une recommandation de vote : il reflète
        uniquement les {answeredCount} énoncés auxquels vous avez répondu et la pondération que
        vous avez choisie.
      </p>
    </div>
  );
}
