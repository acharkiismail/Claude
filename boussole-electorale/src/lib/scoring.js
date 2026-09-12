// Échelle Likert : 1 = fortement en désaccord ... 5 = fortement d'accord.
// null = "cet enjeu n'est pas important pour moi" (exclu du calcul de similarité).

export function computeAffinities(statements, parties, userAnswers, themeWeights) {
  const maxDiff = 4; // écart maximal possible entre deux valeurs 1..5

  return parties
    .map((party) => {
      let weightedSquaredSum = 0;
      let weightedMaxSum = 0;
      let answered = 0;

      for (const statement of statements) {
        const userValue = userAnswers[statement.id];
        if (userValue == null) continue;

        const partyValue = statement.positions[party.id]?.value;
        if (partyValue == null) continue;

        const weight = themeWeights[statement.themeId] ?? 1;
        const diff = userValue - partyValue;

        weightedSquaredSum += weight * diff * diff;
        weightedMaxSum += weight * maxDiff * maxDiff;
        answered += 1;
      }

      const distance = Math.sqrt(weightedSquaredSum);
      const maxDistance = Math.sqrt(weightedMaxSum);
      const affinity = maxDistance > 0 ? (1 - distance / maxDistance) * 100 : 0;

      return {
        partyId: party.id,
        affinity: Math.round(affinity * 10) / 10,
        answered,
      };
    })
    .sort((a, b) => b.affinity - a.affinity);
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

// Profil par enjeu (façon "smartspider") : un score 0-100 par thème, calculé comme
// le degré d'accord moyen avec les énoncés de ce thème. 0 = désaccord total avec
// l'ensemble des énoncés du thème, 100 = accord total.
export function computeThemeScores(statements, themes, answers) {
  const totals = Object.fromEntries(themes.map((t) => [t.id, { sum: 0, count: 0 }]));

  for (const statement of statements) {
    const value = answers[statement.id];
    if (value == null) continue;
    const bucket = totals[statement.themeId];
    bucket.sum += ((value - 1) / 4) * 100;
    bucket.count += 1;
  }

  return Object.fromEntries(
    themes.map((t) => {
      const bucket = totals[t.id];
      return [t.id, bucket.count > 0 ? bucket.sum / bucket.count : null];
    })
  );
}

// Les énoncés où vous et un parti donné convergez ou divergez le plus,
// utilisés pour expliquer "pourquoi ce match" plutôt que de livrer un seul %.
export function computeMatchHighlights(statements, answers, partyId, count = 3) {
  const scored = [];
  for (const statement of statements) {
    const userValue = answers[statement.id];
    const partyValue = statement.positions[partyId]?.value;
    if (userValue == null || partyValue == null) continue;
    scored.push({ statement, userValue, partyValue, gap: Math.abs(userValue - partyValue) });
  }

  const agreements = [...scored].sort((a, b) => a.gap - b.gap).slice(0, count);
  const disagreements = [...scored]
    .sort((a, b) => b.gap - a.gap)
    .slice(0, count)
    .filter((s) => s.gap >= 2);

  return { agreements, disagreements };
}

export function partyAnswersFromPositions(statements, partyId) {
  const answers = {};
  for (const statement of statements) {
    const pos = statement.positions[partyId];
    if (pos) answers[statement.id] = pos.value;
  }
  return answers;
}
