# Collection vers Excel (aplatissement des collections imbriquées)

`CollectionToExcel.cs` est un Code Stage Blue Prism qui écrit une Collection dans
un fichier Excel, sur **une seule feuille**, avec **une ligne par enregistrement
parent**. Les champs des collections imbriquées deviennent des colonnes préfixées
par le nom de la colonne parente.

## Forme du résultat

Collection avec une colonne imbriquée `Emprunteur` (champs `Nom`, `Prenom`). Les
champs enfants deviennent des colonnes préfixées, et les lignes de la
sous-collection **s'empilent vers le bas** :

| No Dossier | Montant | Emprunteur-Nom | Emprunteur-Prenom |
|---|---|---|---|
| D-001 | 1500 | Tremblay | Marie |
| | | Gagnon | Luc |
| | | Roy | Anne |

Les valeurs du parent ne sont écrites qu'une fois, sur la première ligne de son bloc.

Deux sous-collections de tailles différentes sur le même parent sont indépendantes —
chacune s'empile dans ses propres colonnes, sans produit cartésien :

| No Dossier | Emprunteur-Nom | Cautions-Garant |
|---|---|---|
| D-002 | Roy | Banque X |
| | Cote | |
| | Bell | |

L'imbrication est récursive (`Emprunteur-Adresses-Ville`), et **chaque sous-ligne
réserve autant de lignes que ses propres enfants en occupent** — sinon deux
emprunteurs ayant chacun plusieurs adresses se chevaucheraient :

| No Dossier | Emprunteur-Nom | Emprunteur-Adresses-Ville |
|---|---|---|
| D-100 | Roy | Quebec |
| | | Levis |
| | Gagnon | Montreal |

Roy occupe deux lignes parce qu'il a deux adresses, donc Gagnon démarre à la
troisième.

## Pourquoi cette forme

Trois façons d'exporter des collections imbriquées vers Excel, et pourquoi
celle-ci a été retenue :

- **Une feuille par sous-collection**, reliée par une clé — normalisé et sans
  perte, mais le lecteur doit faire des allers-retours entre feuilles, et les
  filtres et tableaux croisés dynamiques ne traversent pas deux feuilles.
- **Aplatir en répétant la ligne parent** (comme un `JOIN` SQL) — les données
  parent sont dupliquées sur chaque ligne enfant : un `SUM` sur une colonne de
  montant donne alors un total faux, multiplié par le nombre d'enfants.
- **Aplatir en colonnes préfixées, enfants empilés vers le bas** (retenu) — les
  valeurs du parent n'apparaissent qu'une fois, donc aucun risque sur les totaux,
  et l'ensemble se lit d'un coup d'œil sur une seule feuille.

Le compromis : la lecture par formule ou tableau croisé est moins directe, puisque
les cellules parent sont vides sur les lignes de continuation. C'est acceptable ici
parce que la collection principale ne contient qu'un enregistrement — le fichier
est un rapport à lire, pas une table à agréger.

## Comment la mise en page est calculée

Le code procède en quatre passes : repérage d'un échantillon de schéma par
collection imbriquée (pour construire l'en-tête même si certaines lignes ont une
sous-collection vide), construction de l'en-tête aplatie, calcul de la hauteur de
chaque enregistrement, puis remplissage.

La hauteur d'une ligne est `max(1, hauteur totale de sa plus grande
sous-collection)`, chaque sous-ligne comptant récursivement sa propre hauteur.
C'est ce calcul qui garantit qu'aucun bloc n'en écrase un autre.

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
