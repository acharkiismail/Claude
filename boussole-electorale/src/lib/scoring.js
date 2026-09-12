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

// Positionne un vecteur de réponses sur deux axes prédéfinis :
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

export function partyAnswersFromPositions(statements, partyId) {
  const answers = {};
  for (const statement of statements) {
    const pos = statement.positions[partyId];
    if (pos) answers[statement.id] = pos.value;
  }
  return answers;
}
