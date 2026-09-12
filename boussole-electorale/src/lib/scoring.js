// Échelle Likert : 1 = fortement en désaccord ... 5 = fortement d'accord.
// Réponse null = "cet enjeu n'est pas important pour moi" → l'énoncé sort du calcul.
// Position de parti avec reliability "unknown" = position non documentée → elle sort
// aussi du calcul, plutôt que d'être traitée comme un centrisme réel. Sans cette
// exclusion, un parti dont les positions sont mal documentées se retrouve au centre
// de chaque échelle et paraît proche de tout le monde.

const MAX_DIFF = 4; // écart maximal entre deux valeurs 1..5

function isCounted(position) {
  return position != null && position.reliability !== "unknown";
}

function normalizedAffinity(weightedSquaredSum, weightedMaxSum) {
  if (weightedMaxSum <= 0) return null;
  const ratio = Math.sqrt(weightedSquaredSum) / Math.sqrt(weightedMaxSum);
  return (1 - ratio) * 100;
}

export function computeAffinities(statements, parties, userAnswers, themeWeights) {
  return parties
    .map((party) => {
      let weightedSquaredSum = 0;
      let weightedMaxSum = 0;
      let counted = 0;

      for (const statement of statements) {
        const userValue = userAnswers[statement.id];
        if (userValue == null) continue;

        const position = statement.positions[party.id];
        if (!isCounted(position)) continue;

        const weight = themeWeights[statement.themeId] ?? 1;
        const diff = userValue - position.value;

        weightedSquaredSum += weight * diff * diff;
        weightedMaxSum += weight * MAX_DIFF * MAX_DIFF;
        counted += 1;
      }

      const affinity = normalizedAffinity(weightedSquaredSum, weightedMaxSum);

      return {
        partyId: party.id,
        affinity: affinity == null ? null : Math.round(affinity * 10) / 10,
        counted,
      };
    })
    .sort((a, b) => (b.affinity ?? -1) - (a.affinity ?? -1));
}

// Affinité par thème (0-100) entre l'utilisateur et un parti : même calcul que
// l'affinité globale, restreint aux énoncés d'un thème. Contrairement à un simple
// "degré d'accord moyen", ce score reste interprétable même quand les énoncés d'un
// thème pointent dans des directions opposées.
export function computeThemeAffinities(statements, themes, answers, partyId) {
  const totals = Object.fromEntries(themes.map((t) => [t.id, { sq: 0, max: 0 }]));

  for (const statement of statements) {
    const userValue = answers[statement.id];
    if (userValue == null) continue;

    const position = statement.positions[partyId];
    if (!isCounted(position)) continue;

    const bucket = totals[statement.themeId];
    const diff = userValue - position.value;
    bucket.sq += diff * diff;
    bucket.max += MAX_DIFF * MAX_DIFF;
  }

  return Object.fromEntries(
    themes.map((t) => {
      const affinity = normalizedAffinity(totals[t.id].sq, totals[t.id].max);
      return [t.id, affinity == null ? null : Math.round(affinity)];
    })
  );
}

// Thèmes réellement évalués : ceux où l'utilisateur a répondu à au moins un énoncé.
// Un thème entièrement passé n'est pas tracé sur le radar plutôt que d'y être
// représenté par une valeur inventée.
export function activeThemes(statements, themes, answers) {
  return themes.filter((theme) =>
    statements.some((s) => s.themeId === theme.id && answers[s.id] != null)
  );
}

// Positionne un vecteur de réponses sur deux axes prédéfinis (vue simplifiée) :
// économique (gauche <-> droite) et identité nationale (fédéraliste <-> souverainiste).
export function computeAxisPosition(statements, answers) {
  const totals = { economic: { sum: 0, count: 0 }, identity: { sum: 0, count: 0 } };

  for (const statement of statements) {
    const value = answers[statement.id];
    if (value == null) continue;

    for (const axis of ["economic", "identity"]) {
      const dir = statement.axis?.[axis] ?? 0;
      if (dir === 0) continue;
      totals[axis].sum += dir * ((value - 3) / 2);
      totals[axis].count += 1;
    }
  }

  return {
    economic: totals.economic.count > 0 ? totals.economic.sum / totals.economic.count : 0,
    identity: totals.identity.count > 0 ? totals.identity.sum / totals.identity.count : 0,
  };
}

// Les énoncés qui expliquent le résultat. Une "convergence" exige un écart d'au plus
// un cran : sans ce filtre, on présenterait un écart de deux crans comme un accord.
export function computeMatchHighlights(statements, answers, partyId, count = 3) {
  const scored = [];
  for (const statement of statements) {
    const userValue = answers[statement.id];
    const position = statement.positions[partyId];
    if (userValue == null || !isCounted(position)) continue;
    scored.push({
      statement,
      userValue,
      partyValue: position.value,
      gap: Math.abs(userValue - position.value),
    });
  }

  const agreements = scored
    .filter((s) => s.gap <= 1)
    .sort((a, b) => a.gap - b.gap)
    .slice(0, count);
  const disagreements = scored
    .filter((s) => s.gap >= 2)
    .sort((a, b) => b.gap - a.gap)
    .slice(0, count);

  return { agreements, disagreements };
}

// Un énoncé sur lequel tous les partis documentés tiennent la même position ne
// départage personne. Plutôt que de le masquer, on le signale : "les cinq partis
// s'entendent" est en soi une information sur la campagne.
export function isConsensus(statement) {
  const values = Object.values(statement.positions)
    .filter(isCounted)
    .map((p) => p.value);
  if (values.length < 2) return false;
  return Math.max(...values) - Math.min(...values) <= 1;
}

// Combien des positions d'un parti sont documentées — affiché pour que le lecteur
// puisse pondérer lui-même la fiabilité du score.
export function computeCompleteness(statements, partyId) {
  const total = statements.length;
  const known = statements.filter((s) => isCounted(s.positions[partyId])).length;
  return { known, total };
}

export function partyAnswersFromPositions(statements, partyId) {
  const answers = {};
  for (const statement of statements) {
    const position = statement.positions[partyId];
    if (isCounted(position)) answers[statement.id] = position.value;
  }
  return answers;
}
