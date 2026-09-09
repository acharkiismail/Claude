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
3. Ajouter un Code Stage sur la page de l'action, langage C#.
4. Ajouter la référence `EPPlus.dll` au Code Stage (NuGet `EPPlus`, puis
   référencer la DLL via l'onglet Références du Code Stage ou System Manager >
   Références).
5. Coller le contenu de `CollectionToExcel.cs` dans l'éditeur de code.

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
