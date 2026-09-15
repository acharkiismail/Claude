// Les articles n'ont pas d'URL vérifiée : la recherche documentaire s'est faite à
// travers des résumés de moteur de recherche, sans jamais ouvrir les pages. Plutôt
// que d'inventer des liens profonds — un lien mort ou qui pointe à côté serait pire
// que pas de lien sur un outil politique — la citation renvoie vers une recherche
// pré-remplie. Elle ne pourrit pas et ne prétend rien.

const OUTLETS = [
  "La Presse",
  "Le Devoir",
  "Radio-Canada",
  "Le Soleil",
  "Les Affaires",
  "Noovo Info",
  "L'actualité",
  "Journal de Sherbrooke",
  "Presse-toi à gauche",
  "CBC",
  "quebec.ca",
  "fedecegeps.ca",
];

const STOPWORDS = new Set([
  "le", "la", "les", "un", "une", "des", "du", "de", "et", "ou", "à", "au", "aux",
  "en", "dans", "pour", "par", "sur", "sans", "avec", "que", "qui", "plutôt", "son",
  "sa", "ses", "leur", "leurs", "est", "sont", "a", "ont", "plus", "moins", "ne",
  "pas", "se", "s", "d", "l", "n", "y", "ce", "cette", "il", "elle",
]);

export function citationOutlet(citation) {
  if (!citation) return null;
  return OUTLETS.find((o) => citation.toLowerCase().includes(o.toLowerCase())) ?? null;
}

export function citationSearchUrl(citation, sourceText = "") {
  const outlet = citationOutlet(citation);
  if (!outlet) return null;

  const keywords = sourceText
    .replace(/[«»(),;:.?!—–"']/g, " ")
    .split(/\s+/)
    .filter((w) => w.length > 3 && !STOPWORDS.has(w.toLowerCase()))
    .slice(0, 7)
    .join(" ");

  const query = `${outlet} ${keywords}`.trim();
  return `https://duckduckgo.com/?q=${encodeURIComponent(query)}`;
}
