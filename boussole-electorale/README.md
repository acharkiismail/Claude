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
  chaque parti une position (échelle 1-5), une source (paraphrasée, non verbatim) et un niveau
  de fiabilité : `sourced`, `inferred`, ou `unknown` (exclu du calcul).
- `src/lib/scoring.js` — calcul de l'affinité (distance euclidienne pondérée, normalisée en %),
  de l'affinité par thème (`computeThemeAffinities`, 0-100 par thème), du positionnement 2D
  simplifié, de la complétude des données par parti (`computeCompleteness`) et des énoncés de
  plus forte convergence/divergence (`computeMatchHighlights`).
- `src/components/` — étapes de l'application (intro, pondération des thèmes, questionnaire,
  résultats) et visualisations (`RadarChart`, `CompassChart`, `RankingChart`).

## Méthodologie

- Énoncés en langage courant : une seule idée par énoncé, mots du quotidien, aucun numéro de
  loi ni terme technocratique (12 mots en moyenne). Le détail technique — ce que fait la loi 21,
  ce qu'est la bourse du carbone — vit dans la ligne de contexte affichée sous l'énoncé, pas
  dans l'énoncé lui-même. C'est la règle du Wahl-O-Mat : une thèse doit être comprise par
  quelqu'un sans bagage politique.
- Échelle Likert à 5 points par énoncé, avec option « cet enjeu n'est pas important pour moi »
  (exclut l'énoncé du calcul plutôt que de le neutraliser à une valeur médiane).
- Pondération optionnelle par thème (poids 1 à 3) appliquée au calcul de distance.
- Affinité par parti = `(1 - distance_pondérée / distance_max_possible) × 100`.
- **Les positions non documentées sont exclues du calcul** (`reliability: "unknown"`), au lieu
  d'être comptées comme une position neutre. C'est le correctif le plus important du modèle : un
  audit sur 4000 électeurs simulés montrait que le PLQ, dont 9 positions manquaient et étaient
  ramenées au centre de l'échelle, arrivait en tête dans 43 % des cas — un artefact de collecte,
  pas de politique. Après recherche ciblée et exclusion des positions restées inconnues, il tombe
  à 24,8 %. Le classement affiche la complétude des données de chaque parti (ex. « 26/30 doc. »).
- Affinité par thème (radar) : le même calcul de distance, restreint aux énoncés d'un thème,
  donne un score 0-100 par thème et par parti. Un score d'accord moyen a été écarté : dans trois
  thèmes, les énoncés pointent dans des directions opposées, si bien qu'un répondant disant
  « oui » à tout obtenait 100/100 — l'axe mesurait l'acquiescement, pas une position.
- Les écarts de moins de 2 points entre deux partis sont annoncés comme non significatifs plutôt
  que tranchés. Seuil calibré : pour un électeur cohérent (même bruité à 40 %), le bon parti
  arrive en tête avec ~30 points d'avance et la mention « serré » ne se déclenche jamais.
- Positionnement 2D (vue simplifiée additionnelle) calculé uniquement à partir des énoncés
  pertinents à chaque axe (économique / identité nationale), pas une ACP complète.
- « Pourquoi ce match » met en avant les énoncés de plus forte convergence (écart d'au plus un
  cran) et de plus forte divergence avec le parti en tête, plutôt qu'un pourcentage global.
- Les énoncés sur lesquels tous les partis s'entendent sont signalés comme tels : ils ne
  départagent personne, mais le consensus est en soi une information sur la campagne.
- Chaque position de parti cite sa source (plateforme officielle 2026 lorsque disponible,
  bilan législatif, ou déclaration publique récente du chef) et un badge « Sourcé », « Déduit »
  ou « Non documenté » — voir « Détail par enjeu et sources » dans les résultats.
- La palette des 5 partis passe par le validateur de la compétence `dataviz` (séparation sous
  daltonisme, contraste, bande de luminosité). Deux écarts assumés : le bleu très foncé du PCQ
  sort de la bande de luminosité en mode clair (c'est le choix de marque), et en mode sombre le
  bleu du PQ et l'indigo du PCQ sont séparés d'un ΔE de 10,9, sous le plancher de 15. Dans les
  deux cas la couleur n'est jamais le seul indice : chaque barre, point et radar porte le sigle
  du parti en toutes lettres.
- Version courte : les 8 énoncés au plus fort écart-type entre partis, un par thème. C'est la
  porte d'entrée par défaut — un visiteur arrivé d'un lien social abandonne devant 30 questions,
  et qui abandonne ne partage pas.
- Le résultat s'encode dans l'URL (un caractère par énoncé, un par thème). Un lien partagé
  reproduit exactement le résultat de son auteur et invite le visiteur à faire le sien. Aucun
  serveur, aucun stockage, aucune donnée qui quitte le navigateur.
- La carte de partage (1080×1080) est dessinée en canvas côté client, sur une palette claire
  figée pour que l'image ait la même allure quel que soit le thème de celui qui l'a produite.

## État des données (relevé le 12 septembre 2026)

| Parti | Sourcé | Déduit | Non documenté |
|---|---|---|---|
| CAQ | 29 | 1 | 0 |
| PQ | 30 | 0 | 0 |
| PLQ | 24 | 2 | 4 |
| QS | 29 | 1 | 0 |
| PCQ | 29 | 0 | 1 |

Les cinq positions « non documentées » ne sont pas des trous de collecte mais des absences
de position publique : le PLQ n'avait pas publié de plateforme environnementale complète à la
fin août 2026 (d'où l'absence de position sur les nouveaux barrages, la propriété
d'Hydro-Québec et les mégaprojets industriels), et la plateforme du PCQ ne s'exprime pas sur
la propriété d'Hydro-Québec.

## Limites connues

La campagne étant en cours, les positions évoluent — d'où la date de relevé affichée dans
l'application. Deux énoncés départagent faiblement les partis (le plein contrôle de
l'immigration, sur lequel les cinq s'entendent, et les infrastructures scolaires) : ils sont
conservés parce que le consensus est une information, et signalés comme tels dans les
résultats. Cet outil est une simplification à visée pédagogique, pas un sondage scientifique
ni un outil de recommandation de vote.
