# Repère — Élections québécoises 2026

Outil web interactif permettant de découvrir son affinité avec les 5 principaux partis en
lice pour l'élection générale québécoise du 5 octobre 2026 (CAQ, PQ, PLQ, QS, PCQ), à partir
de 30 énoncés répartis sur 10 enjeux de campagne. La méthodologie s'inspire de
[smartvote](https://www.smartvote.ch) (Suisse) et du [Wahl-O-Mat](https://www.wahl-o-mat.de)
(Allemagne), plutôt que de reproduire un outil existant : énoncés à fort pouvoir
discriminant entre partis, contexte factuel par énoncé, pondération par thème, et un profil
par enjeu façon « smartspider » plutôt qu'un score global unique.

## Démarrer

```bash
npm install
npm run dev      # serveur de développement
npm run build    # build de production dans dist/
```

## Structure

- `src/data/parties.json` — les 5 partis (nom, chef, référence de couleur CSS).
- `src/data/themes.json` — les 10 thèmes de l'élection (utilisés aussi comme axes du radar).
- `src/data/statements.json` — les 30 énoncés, chacun avec un `context` factuel, et pour
  chaque parti une position documentée (échelle 1-5), une source (paraphrasée, non verbatim)
  et un niveau de fiabilité (`sourced` ou `inferred`).
- `src/lib/scoring.js` — calcul de l'affinité (distance euclidienne pondérée, normalisée en %),
  du profil par enjeu (`computeThemeScores`, 0-100 par thème), du positionnement 2D simplifié,
  et des énoncés de plus forte convergence/divergence avec un parti (`computeMatchHighlights`).
- `src/components/` — étapes de l'application (intro, pondération des thèmes, questionnaire,
  résultats) et visualisations (`RadarChart`, `CompassChart`, `RankingChart`).

## Méthodologie

- Échelle Likert à 5 points par énoncé, avec option « cet enjeu n'est pas important pour moi »
  (exclut l'énoncé du calcul plutôt que de le neutraliser à une valeur médiane).
- Pondération optionnelle par thème (poids 1 à 3) appliquée au calcul de distance.
- Affinité par parti = `(1 - distance_pondérée / distance_max_possible) × 100`.
- Profil par enjeu (radar) : un score 0-100 par thème représentant le degré d'accord moyen
  avec les énoncés de ce thème, affiché pour l'utilisateur seul puis superposé à chaque parti —
  la vue la plus complète, puisqu'elle couvre les 10 enjeux plutôt que 2 axes agrégés.
- Positionnement 2D (vue simplifiée additionnelle) calculé uniquement à partir des énoncés
  pertinents à chaque axe (économique / identité nationale), pas une ACP complète.
- « Pourquoi ce match » met en avant les 3 énoncés de plus forte convergence et de plus forte
  divergence avec le parti en tête, plutôt que de s'arrêter à un pourcentage global.
- Chaque position de parti cite sa source (plateforme officielle 2026 lorsque disponible,
  bilan législatif, ou déclaration publique récente du chef) et un badge « Sourcé »/« Déduit »
  indiquant si elle repose sur une source directe ou sur l'orientation générale du parti faute
  d'engagement chiffré trouvé — voir la section « Détail par enjeu et sources » des résultats.
- La palette des 5 partis a été choisie et validée (séparation de teinte pour daltoniens,
  contraste, bande de luminosité) plutôt que reprise telle quelle des couleurs de marque, qui
  se recoupent trop (CAQ/PQ/PCQ sont toutes des bleus); l'identification reste toujours faite
  par un nom écrit à côté de la couleur, jamais par la couleur seule.

## Limites connues

Certaines positions, faute de plateforme complète publiée au moment de la recherche ou
d'un accès direct au site officiel du parti (plusieurs sites étaient bloqués depuis
l'environnement de recherche), sont déduites de l'orientation générale du parti plutôt que
d'un engagement chiffré précis; ces cas sont marqués `"reliability": "inferred"` dans les
données et affichés avec un badge « Déduit » dans l'interface. Cet outil est une
simplification à visée pédagogique, pas un sondage scientifique ni un outil de recommandation
de vote.
