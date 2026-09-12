# Boussole électorale — Élections québécoises 2026

Outil web interactif permettant de découvrir son affinité avec les 5 principaux partis en
lice pour l'élection générale québécoise du 5 octobre 2026 (CAQ, PQ, PLQ, QS, PCQ), à partir
de 30 énoncés répartis sur 10 enjeux de campagne.

## Démarrer

```bash
npm install
npm run dev      # serveur de développement
npm run build    # build de production dans dist/
```

## Structure

- `src/data/parties.json` — les 5 partis (nom, chef, couleur).
- `src/data/themes.json` — les 10 thèmes de l'élection.
- `src/data/statements.json` — les 30 énoncés, avec pour chacun la position documentée de
  chaque parti (échelle 1-5) et une source (paraphrasée, non verbatim).
- `src/lib/scoring.js` — calcul de l'affinité (distance euclidienne pondérée, normalisée en %)
  et du positionnement sur les deux axes prédéfinis (économique / identité nationale).
- `src/components/` — étapes de l'application (intro, pondération des thèmes, questionnaire,
  résultats).

## Méthodologie

- Échelle Likert à 5 points par énoncé, avec option « cet enjeu n'est pas important pour moi »
  (exclut l'énoncé du calcul plutôt que de le neutraliser à une valeur médiane).
- Pondération optionnelle par thème (poids 1 à 3) appliquée au calcul de distance.
- Affinité par parti = `(1 - distance_pondérée / distance_max_possible) × 100`.
- Positionnement 2D calculé uniquement à partir des énoncés pertinents à chaque axe (pas une
  ACP complète) — une simplification visuelle, pas une représentation exhaustive des 10 enjeux.
- Chaque position de parti cite sa source (plateforme officielle 2026 lorsque disponible,
  bilan législatif, ou déclaration publique récente du chef) — voir la section « Détail par
  enjeu et sources » des résultats.

## Limites connues

Certaines positions, faute de plateforme complète publiée au moment de la recherche ou
d'un accès direct au site officiel du parti (plusieurs sites étaient bloqués depuis
l'environnement de recherche), sont déduites de l'orientation générale du parti plutôt que
d'un engagement chiffré précis; ces cas sont identifiés explicitement dans la source citée.
Cet outil est une simplification à visée pédagogique, pas un sondage scientifique.
