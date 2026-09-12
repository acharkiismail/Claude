// Le résultat tient dans l'URL : un caractère par énoncé (0 = sans réponse ou
// enjeu écarté, 1-5 = position) puis un caractère par thème pour la pondération.
// Un lien partagé reproduit donc exactement le résultat de son auteur, sans
// serveur ni stockage — et permet à quelqu'un de comparer le sien.

const SEPARATOR = ".";

export function encodeResult(statements, themes, answers, weights) {
  const answerPart = statements
    .map((s) => {
      const value = answers[s.id];
      return value == null ? "0" : String(value);
    })
    .join("");
  const weightPart = themes.map((t) => String(weights[t.id] ?? 1)).join("");
  return `${answerPart}${SEPARATOR}${weightPart}`;
}

export function decodeResult(encoded, statements, themes) {
  if (typeof encoded !== "string") return null;
  const [answerPart, weightPart] = encoded.split(SEPARATOR);
  if (!answerPart || answerPart.length !== statements.length) return null;
  if (!weightPart || weightPart.length !== themes.length) return null;
  if (!/^[0-5]+$/.test(answerPart) || !/^[1-3]+$/.test(weightPart)) return null;

  const answers = {};
  statements.forEach((statement, i) => {
    const digit = Number(answerPart[i]);
    if (digit >= 1 && digit <= 5) answers[statement.id] = digit;
    else answers[statement.id] = null;
  });

  const weights = {};
  themes.forEach((theme, i) => {
    weights[theme.id] = Number(weightPart[i]);
  });

  // Un lien sans aucune réponse exploitable ne vaut pas la peine d'être restauré.
  if (!Object.values(answers).some((v) => v != null)) return null;

  return { answers, weights };
}

export function resultUrl(encoded) {
  const { origin, pathname } = window.location;
  return `${origin}${pathname}#r=${encoded}`;
}

export function readResultFromHash() {
  const match = window.location.hash.match(/^#r=(.+)$/);
  return match ? decodeURIComponent(match[1]) : null;
}

export function clearHash() {
  window.history.replaceState(null, "", window.location.pathname + window.location.search);
}
