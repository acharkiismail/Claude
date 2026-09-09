// Blue Prism Code Stage — Object Studio action "Write Collection To Excel"
//
// Wiring in Blue Prism (Code Stage > onglet Inputs/Outputs) — les noms C# ci-dessous doivent
// correspondre EXACTEMENT à la colonne "Name" de cet onglet. Blue Prism remplace les espaces
// par des underscores, donc un Data Item "File Path" devient la variable C# `File_Path` :
//   Inputs:
//     Collection  (Collection) -> variable C# `Collection`  (System.Data.DataTable)
//     File Path   (Text)       -> variable C# `File_Path`   (string)
//     Sheet Name  (Text, opt.) -> variable C# `Sheet_Name`  (string)
//   Outputs:
//     Sheets Written (Text)    -> variable C# `Sheets_Written` (string, liste séparée par des virgules)
//
// Le code ci-dessous n'a besoin :
//   - d'AUCUNE référence d'assembly (Excel est piloté en COM tardif via le ProgID
//     "Excel.Application" ; il faut seulement qu'Excel soit installé sur la machine) ;
//   - d'AUCUN namespace à déclarer : tous les types sont écrits en nom complet
//     (System.Collections.Generic.List<string>, System.Runtime.InteropServices.Marshal, ...).
//
//   Le Code Stage ne référence que mscorlib / System / System.Data : rien de ce qui vit dans
//   System.Core.dll n'est utilisé — ni LINQ, ni HashSet<T>. Seul List<T> (mscorlib) sert de
//   registre de noms de feuilles, avec une comparaison insensible à la casse faite à la main.
//
// À coller tel quel dans la zone de code du Code Stage, en commençant à la ligne
// `Sheets_Written = "";` — sans lignes `using`, sans méthode englobante, et sans modificateur
// d'accès (`private`/`public`) sur les fonctions en bas : Blue Prism compile ce texte comme le
// corps de sa propre méthode générée.
//
// Blue Prism stocke un champ de type Collection imbriquée comme une valeur System.Data.DataTable
// dans la cellule de la DataTable parente : une colonne dont le DataType est DataTable est donc
// une collection imbriquée, et c'est ce qui déclenche l'écriture dans une feuille dédiée.

Sheets_Written = "";

if (Collection == null)
    throw new System.InvalidOperationException("La collection d'entrée n'est pas initialisée.");
if (File_Path == null || File_Path.Trim().Length == 0)
    throw new System.InvalidOperationException("File Path est obligatoire.");

System.Type xlType = System.Type.GetTypeFromProgID("Excel.Application");
if (xlType == null)
    throw new System.InvalidOperationException("Microsoft Excel n'est pas installe sur cette machine (ProgID 'Excel.Application' introuvable).");

string rootSheet = (Sheet_Name == null || Sheet_Name.Trim().Length == 0) ? "Data" : Sheet_Name;

// List<> plutot que HashSet<> : HashSet<T> vit dans System.Core.dll, que le Code Stage
// Blue Prism ne reference pas par defaut, alors que List<T> est dans mscorlib.
System.Collections.Generic.List<string> sheetsCreated =
    new System.Collections.Generic.List<string>();

object xlApp = null;
object xlBooks = null;
object xlBook = null;

try
{
    xlApp = System.Activator.CreateInstance(xlType);
    SetProp(xlApp, "Visible", false);
    SetProp(xlApp, "DisplayAlerts", false);

    xlBooks = GetProp(xlApp, "Workbooks");
    xlBook = Invoke(xlBooks, "Add");

    WriteTable(xlBook, Collection, rootSheet, sheetsCreated, -1);

    // Workbooks.Add() cree un classeur avec une feuille vide : on supprime tout ce qu'on n'a pas ecrit.
    object bookSheets = GetProp(xlBook, "Sheets");
    int bookSheetCount = System.Convert.ToInt32(GetProp(bookSheets, "Count"));
    for (int idx = bookSheetCount; idx >= 1; idx--)
    {
        object oneSheet = GetProp(bookSheets, "Item", idx);
        string oneSheetName = System.Convert.ToString(GetProp(oneSheet, "Name"));
        if (!ContainsIgnoreCase(sheetsCreated, oneSheetName))
            Invoke(oneSheet, "Delete");
        System.Runtime.InteropServices.Marshal.ReleaseComObject(oneSheet);
    }
    System.Runtime.InteropServices.Marshal.ReleaseComObject(bookSheets);

    // 51 = xlOpenXMLWorkbook (.xlsx)
    Invoke(xlBook, "SaveAs", File_Path, 51);
    Sheets_Written = string.Join(",", sheetsCreated.ToArray());
}
finally
{
    if (xlBook != null)
    {
        Invoke(xlBook, "Close", false);
        System.Runtime.InteropServices.Marshal.ReleaseComObject(xlBook);
    }
    if (xlBooks != null)
        System.Runtime.InteropServices.Marshal.ReleaseComObject(xlBooks);
    if (xlApp != null)
    {
        Invoke(xlApp, "Quit");
        System.Runtime.InteropServices.Marshal.ReleaseComObject(xlApp);
    }
    System.GC.Collect();
    System.GC.WaitForPendingFinalizers();
}

// Ecrit une DataTable dans sa propre feuille, puis descend recursivement dans chaque colonne
// de type collection imbriquee pour lui donner sa propre feuille a son tour.
// parentKey vaut -1 pour la collection racine (pas de colonne ParentRowKey).
void WriteTable(object wb, System.Data.DataTable tbl, string wantedName,
    System.Collections.Generic.List<string> createdList, int parentKey)
{
    string newSheetName = MakeUniqueSheetName(wantedName, createdList);

    object wsSheets = GetProp(wb, "Sheets");
    int wsCount = System.Convert.ToInt32(GetProp(wsSheets, "Count"));
    object afterSh = GetProp(wsSheets, "Item", wsCount);
    object newWs = Invoke(wsSheets, "Add", System.Type.Missing, afterSh, System.Type.Missing, System.Type.Missing);
    SetProp(newWs, "Name", newSheetName);
    System.Runtime.InteropServices.Marshal.ReleaseComObject(afterSh);
    System.Runtime.InteropServices.Marshal.ReleaseComObject(wsSheets);

    System.Collections.Generic.List<string> nestedCols = new System.Collections.Generic.List<string>();
    System.Collections.Generic.List<System.Data.DataColumn> flatCols =
        new System.Collections.Generic.List<System.Data.DataColumn>();
    foreach (System.Data.DataColumn col in tbl.Columns)
    {
        if (col.DataType == typeof(System.Data.DataTable))
            nestedCols.Add(col.ColumnName);
        else
            flatCols.Add(col);
    }

    int keyCols = (parentKey >= 0) ? 2 : 1;
    int colCount = keyCols + flatCols.Count;
    int rowCount = tbl.Rows.Count + 1;
    object[,] grid = new object[rowCount, colCount];

    if (parentKey >= 0)
    {
        grid[0, 0] = "ParentRowKey";
        grid[0, 1] = "RowKey";
    }
    else
    {
        grid[0, 0] = "RowKey";
    }
    for (int ci = 0; ci < flatCols.Count; ci++)
        grid[0, keyCols + ci] = flatCols[ci].ColumnName;

    for (int ri = 0; ri < tbl.Rows.Count; ri++)
    {
        System.Data.DataRow dr = tbl.Rows[ri];
        int rowNum = ri + 1;

        if (parentKey >= 0)
        {
            grid[rowNum, 0] = parentKey;
            grid[rowNum, 1] = rowNum;
        }
        else
        {
            grid[rowNum, 0] = rowNum;
        }

        for (int ci = 0; ci < flatCols.Count; ci++)
            grid[rowNum, keyCols + ci] = ToCellValue(dr[flatCols[ci]]);
    }

    object topLeft = GetProp(newWs, "Cells", 1, 1);
    object bottomRight = GetProp(newWs, "Cells", rowCount, colCount);
    object rng = GetProp(newWs, "Range", topLeft, bottomRight);
    SetProp(rng, "Value2", grid);
    object rngCols = GetProp(rng, "Columns");
    Invoke(rngCols, "AutoFit");
    System.Runtime.InteropServices.Marshal.ReleaseComObject(rngCols);
    System.Runtime.InteropServices.Marshal.ReleaseComObject(rng);
    System.Runtime.InteropServices.Marshal.ReleaseComObject(bottomRight);
    System.Runtime.InteropServices.Marshal.ReleaseComObject(topLeft);
    System.Runtime.InteropServices.Marshal.ReleaseComObject(newWs);

    for (int ri = 0; ri < tbl.Rows.Count; ri++)
    {
        System.Data.DataRow dr = tbl.Rows[ri];
        foreach (string nestedName in nestedCols)
        {
            if (dr[nestedName] is System.Data.DataTable)
            {
                System.Data.DataTable nestedTbl = (System.Data.DataTable)dr[nestedName];
                WriteTable(wb, nestedTbl, newSheetName + "_" + nestedName, createdList, ri + 1);
            }
        }
    }
}

// Une collection Blue Prism peut contenir des types qu'Excel refuse (Image, Binary, Password,
// TimeSpan) : tout ce qui n'est pas nativement ecrivable part en texte.
object ToCellValue(object raw)
{
    if (raw == null || raw is System.DBNull)
        return null;
    if (raw is string || raw is bool || raw is System.DateTime
        || raw is int || raw is long || raw is short || raw is byte
        || raw is double || raw is float || raw is decimal)
        return raw;
    return raw.ToString();
}

// Comparaison insensible a la casse sans HashSet<> ni LINQ (tous deux dans System.Core.dll,
// non reference par le Code Stage) : la liste des feuilles reste tres courte.
bool ContainsIgnoreCase(System.Collections.Generic.List<string> haystack, string needle)
{
    for (int n = 0; n < haystack.Count; n++)
    {
        if (string.Equals(haystack[n], needle, System.StringComparison.OrdinalIgnoreCase))
            return true;
    }
    return false;
}

// Noms de feuille Excel : 31 caracteres max, pas de [ ] * ? : / \, et uniques dans le classeur.
// Le nom retenu est ajoute a usedList : la liste sert a la fois de registre d'unicite et de
// liste des feuilles creees (renvoyee dans Sheets_Written).
string MakeUniqueSheetName(string wanted, System.Collections.Generic.List<string> usedList)
{
    string clean = "";
    if (wanted != null)
    {
        for (int k = 0; k < wanted.Length; k++)
        {
            char ch = wanted[k];
            if (ch != '[' && ch != ']' && ch != '*' && ch != '?' && ch != ':' && ch != '/' && ch != '\\')
                clean = clean + ch;
        }
    }
    clean = clean.Trim();
    if (clean.Length == 0)
        clean = "Sheet";
    if (clean.Length > 31)
        clean = clean.Substring(0, 31);

    string candidate = clean;
    int sfx = 1;
    while (ContainsIgnoreCase(usedList, candidate))
    {
        string sfxText = "_" + sfx.ToString();
        sfx++;
        int keepLen = clean.Length;
        if (keepLen > 31 - sfxText.Length)
            keepLen = 31 - sfxText.Length;
        candidate = clean.Substring(0, keepLen) + sfxText;
    }
    usedList.Add(candidate);
    return candidate;
}

// --- Appels COM en liaison tardive : evite toute reference a Microsoft.Office.Interop.Excel ---

object Invoke(object comObj, string memberName, params object[] argv)
{
    return comObj.GetType().InvokeMember(memberName,
        System.Reflection.BindingFlags.InvokeMethod, null, comObj, argv);
}

object GetProp(object comObj, string memberName, params object[] argv)
{
    return comObj.GetType().InvokeMember(memberName,
        System.Reflection.BindingFlags.GetProperty, null, comObj, argv);
}

void SetProp(object comObj, string memberName, object val)
{
    comObj.GetType().InvokeMember(memberName,
        System.Reflection.BindingFlags.SetProperty, null, comObj, new object[] { val });
}
