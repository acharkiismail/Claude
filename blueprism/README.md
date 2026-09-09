# Collection vers Excel (aplatissement des collections imbriquées)

`CollectionToExcel.cs` est un Code Stage Blue Prism qui écrit une Collection dans
un fichier Excel, sur **une seule feuille**, avec **une ligne par enregistrement
parent**. Les champs des collections imbriquées deviennent des colonnes préfixées
par le nom de la colonne parente.

## Forme du résultat

Collection `Emprunts`, avec une colonne imbriquée `Liste Emprunteur` (champs `Nom`, `Prenom`) :

Si aucune ligne n'a plus d'un emprunteur — pas de numéro :

| No Dossier | Montant | Liste Emprunteur-Nom | Liste Emprunteur-Prenom |
|---|---|---|---|
| D-001 | 1500 | Tremblay | Marie |
| D-002 | 2300 | Gagnon | Luc |

Si au moins une ligne en a plusieurs (2 au maximum sur tout l'export) — numérotation,
et les lignes qui en ont moins laissent simplement les cases vides :

| No Dossier | Montant | Liste Emprunteur-1-Nom | Liste Emprunteur-1-Prenom | Liste Emprunteur-2-Nom | Liste Emprunteur-2-Prenom |
|---|---|---|---|---|---|
| D-001 | 1500 | Tremblay | Marie | | |
| D-002 | 2300 | Gagnon | Luc | Roy | Anne |

L'imbrication est récursive : une sous-collection dans une sous-collection donne
`Liste Emprunteur-Adresses-1-Ville`, `Liste Emprunteur-Adresses-2-Ville`, etc.

## Pourquoi cette forme

Trois façons d'exporter des collections imbriquées vers Excel, et pourquoi
celle-ci a été retenue :

- **Une feuille par sous-collection**, reliée par une clé — normalisé et sans
  perte, mais le lecteur doit faire des allers-retours entre feuilles, et les
  filtres et tableaux croisés dynamiques ne traversent pas deux feuilles.
- **Aplatir en répétant la ligne parent** (comme un `JOIN` SQL) — une ligne par
  élément enfant. Excel redevient pleinement utilisable, mais les données parent
  sont dupliquées : un `SUM` sur une colonne de montant donne un total faux,
  multiplié par le nombre d'enfants. Erreur silencieuse et coûteuse.
- **Aplatir en colonnes** (retenu) — une ligne par enregistrement parent, les
  enfants en colonnes. Aucune duplication de ligne, donc aucun risque sur les
  totaux, et tout reste filtrable et lisible d'un coup d'œil.

Le compromis : le nombre de colonnes croît avec le nombre maximum d'éléments
imbriqués. Le code refuse l'export au-delà de la limite Excel de 16 384 colonnes,
avec un message explicite plutôt qu'une erreur COM obscure.

## Comment le nombre de créneaux est décidé

Le maximum est calculé sur **tout l'export**, pas ligne par ligne — sinon une
ligne à 1 emprunteur produirait `Liste Emprunteur-Nom` et une ligne à 2
produirait `Liste Emprunteur-1-Nom`, deux colonnes différentes, et les données ne
s'aligneraient pas. Le code fait donc trois passes : recensement des maximums,
construction de l'en-tête, puis remplissage.

## Mise en place dans Blue Prism

1. Créer un nouvel objet (VBO), ex. `Utility - Collection vers Excel`.
2. Dans Object Studio, ajouter une Action `Write Collection To Excel` avec :
   - **Entrées** : `Collection` (Collection), `File Path` (Texte),
     `Sheet Name` (Texte, optionnel — nom de la feuille, "Data" par défaut)
   - **Sorties** : `Sheets Written` (Texte — nom de la feuille écrite)
3. Ajouter un Code Stage sur la page de l'action, langage C#, et mapper ces mêmes
   paramètres dans son onglet **Inputs/Outputs**.
4. **Aucune référence, aucun namespace à ajouter.** Le code pilote Excel en
   liaison tardive (`Type.GetTypeFromProgID("Excel.Application")` + réflexion),
   et tous les types sont écrits en nom complet. Il n'utilise que les assemblies
   déjà référencées par le Code Stage (mscorlib, System, System.Data) — rien de
   ce qui vit dans `System.Core.dll`, donc ni LINQ, ni `HashSet<T>`, ni
   `Dictionary<,>` (d'où l'emploi de `System.Collections.Hashtable`).
5. Coller le contenu de `CollectionToExcel.cs` dans l'éditeur de code, **à partir
   de la ligne `Sheets_Written = "";`**.

## Pièges du Code Stage Blue Prism (causes d'erreurs de compilation)

Blue Prism compile le texte du Code Stage comme le **corps de sa propre méthode
générée**. Les erreurs rencontrées à la mise en place, et leur cause réelle :

| Erreur | Cause | Correctif appliqué |
|---|---|---|
| `Syntax error, '(' expected` | lignes `using` collées dans la zone de code | aucun `using` : types en nom complet |
| `The modifier 'private' is not valid for this item` | méthodes déclarées avec un modificateur d'accès (elles deviennent des fonctions locales) | méthodes sans `private`/`public` |
| `The name 'Marshal'/'BindingFlags'/'List<>' does not exist` | namespaces non importés | types en nom complet |
| `'HashSet<>' does not exist in the namespace 'System.Collections.Generic'` | `HashSet<T>`, `Dictionary<,>` et LINQ vivent dans `System.Core.dll`, que le Code Stage ne référence pas (contrairement à `List<T>`, dans mscorlib) | `Hashtable` et `List<string>` uniquement |
| `A local or parameter named 'workbook' cannot be declared in this scope` | un paramètre de fonction locale porte le même nom qu'une variable du corps principal | noms distincts entre les deux portées |
| `The out parameter 'Sheets_Written' must be assigned...` | Blue Prism remplace les espaces des Data Items par des underscores | variables `File_Path`, `Sheet_Name`, `Sheets_Written` |

**Important sur les noms** : si vos Data Items s'appellent `File Path` / `Sheet Name` /
`Sheets Written`, Blue Prism génère les variables C# `File_Path` / `Sheet_Name` /
`Sheets_Written` — c'est ce que le code utilise. Si vous les nommez autrement,
adaptez soit les noms dans l'onglet Inputs/Outputs, soit les références dans le code.

## Repérage des collections imbriquées

En interne, Blue Prism stocke un champ de type Collection comme une valeur
`System.Data.DataTable` dans la cellule de la DataTable parente. Le code détecte
donc une colonne imbriquée quand `DataColumn.DataType == typeof(DataTable)`.

## Prérequis

Microsoft Excel doit être installé sur la machine (design ET Runtime Resource
qui exécutera le process). Le code démarre une instance Excel invisible
(`Visible = false`), écrit les données, sauvegarde en `.xlsx`, puis ferme
proprement l'instance et libère les objets COM dans le bloc `finally` — pas de
processus `EXCEL.EXE` orphelin en fonctionnement normal.

Les types qu'Excel ne sait pas écrire (Image, Binary, Password, TimeSpan) sont
convertis en texte plutôt que de faire échouer l'export.
