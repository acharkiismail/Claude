# Collection vers Excel (avec collections imbriquées)

`CollectionToExcel.cs` est un Code Stage Blue Prism qui écrit une Collection dans
un fichier Excel. Si un champ de la Collection est lui-même une Collection
(collection imbriquée), il est écrit dans une feuille séparée plutôt que d'être
aplati dans la feuille principale — et ce récursivement pour les niveaux
d'imbrication multiples.

## Pourquoi un Code Stage plutôt que Process Studio

Une Collection imbriquée dans Process Studio (boucle dans une boucle) fonctionne
pour un seul niveau, mais devient vite ingérable dès qu'il y a plusieurs champs
Collection ou plusieurs niveaux d'imbrication. Le code C# gère n'importe quelle
profondeur sans stage supplémentaire à chaque fois qu'un nouveau champ imbriqué
apparaît dans les données.

## Mise en place dans Blue Prism

1. Créer un nouvel objet (VBO), ex. `Utility - Collection vers Excel`.
2. Dans Object Studio, ajouter une Action `Write Collection To Excel` avec :
   - **Entrées** : `Collection` (Collection), `File Path` (Texte),
     `Sheet Name` (Texte, optionnel — nom de la feuille racine, "Data" par défaut)
   - **Sorties** : `Sheets Written` (Texte — liste des feuilles créées, séparées
     par des virgules, utile pour tracer ce qui a été généré)
3. Ajouter un Code Stage sur la page de l'action, langage C#, et mapper ces mêmes
   paramètres dans son onglet **Inputs/Outputs**.
4. **Aucune référence, aucun namespace à ajouter.** Le code pilote Excel en
   liaison tardive (`Type.GetTypeFromProgID("Excel.Application")` + réflexion),
   et tous les types sont écrits en nom complet (`System.Collections.Generic.List<string>`,
   `System.Runtime.InteropServices.Marshal`, ...) sans aucune méthode LINQ.
5. Coller le contenu de `CollectionToExcel.cs` dans l'éditeur de code, **à partir
   de la ligne `Sheets_Written = "";`**.

## Pièges du Code Stage Blue Prism (causes d'erreurs de compilation)

Blue Prism compile le texte du Code Stage comme le **corps de sa propre méthode
générée**. Trois conséquences, qui sont les erreurs rencontrées à la mise en place :

| Erreur | Cause | Correctif appliqué |
|---|---|---|
| `Syntax error, '(' expected` | lignes `using` collées dans la zone de code | aucun `using` : types en nom complet |
| `The modifier 'private' is not valid for this item` | méthodes déclarées avec un modificateur d'accès (elles deviennent des fonctions locales) | méthodes sans `private`/`public` |
| `The name 'Marshal'/'BindingFlags'/'HashSet<>' does not exist` | namespaces non importés | types en nom complet, LINQ supprimé |
| `A local or parameter named 'workbook' cannot be declared in this scope` | un paramètre de fonction locale porte le même nom qu'une variable du corps principal | noms distincts partout (`xlBook` / `wb`, ...) |
| `The out parameter 'Sheets_Written' must be assigned...` | Blue Prism remplace les espaces des Data Items par des underscores | variables `File_Path`, `Sheet_Name`, `Sheets_Written` |

**Important sur les noms** : si vos Data Items s'appellent `File Path` / `Sheet Name` /
`Sheets Written`, Blue Prism génère les variables C# `File_Path` / `Sheet_Name` /
`Sheets_Written` — c'est ce que le code utilise. Si vous les nommez autrement,
adaptez soit les noms dans l'onglet Inputs/Outputs, soit les références dans le code.

## Repérage des collections imbriquées

En interne, Blue Prism stocke un champ de type Collection comme une valeur
`System.Data.DataTable` dans la cellule de la DataTable parente. Le code
détecte donc une colonne imbriquée quand `DataColumn.DataType == typeof(DataTable)`,
et lui donne sa propre feuille nommée `<feuille parente>_<nom du champ>`.

## Traçabilité entre feuilles

Chaque feuille (sauf la racine) reçoit une colonne `ParentRowKey` qui référence
la colonne `RowKey` de la feuille parente, pour pouvoir recoller les données
après export si besoin.

## Limites de nommage Excel gérées

- 31 caractères max par nom de feuille (troncature automatique)
- caractères interdits `[ ] * ? : / \` retirés
- doublons de noms rendus uniques (`_1`, `_2`, ...)

## Prérequis

Microsoft Excel doit être installé sur la machine (design ET Runtime Resource
qui exécutera le process). Le code démarre une instance Excel invisible
(`Visible = false`), écrit les données, sauvegarde en `.xlsx`, puis ferme
proprement l'instance et libère les objets COM dans le bloc `finally` — pas de
processus `EXCEL.EXE` orphelin en fonctionnement normal.
