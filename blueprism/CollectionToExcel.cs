// Blue Prism Code Stage — Object Studio action "Write Collection To Excel"
//
// Aplatit une collection (y compris ses collections imbriquees) dans UNE SEULE feuille Excel :
// une ligne par enregistrement parent, et chaque champ d'une sous-collection devient une colonne
// prefixee par le nom de la colonne parente.
//
//   Collection "Emprunts" avec une colonne imbriquee "Liste Emprunteur" (champs Nom, Prenom) :
//     - si aucune ligne n'a plus d'un emprunteur :
//         No Dossier | Date | Liste Emprunteur-Nom | Liste Emprunteur-Prenom
//     - si au moins une ligne en a plusieurs (ici 2 au maximum sur tout l'export) :
//         No Dossier | Date | Liste Emprunteur-1-Nom | Liste Emprunteur-1-Prenom
//                           | Liste Emprunteur-2-Nom | Liste Emprunteur-2-Prenom
//
// Le nombre de creneaux est calcule sur TOUT l'export (pas ligne par ligne), sinon les colonnes
// ne s'aligneraient pas d'une ligne a l'autre. L'imbrication est recursive : une sous-collection
// dans une sous-collection donne "Parent-1-Enfant-2-Champ".
//
// Wiring in Blue Prism (Code Stage > onglet Inputs/Outputs) — les noms C# ci-dessous doivent
// correspondre EXACTEMENT a la colonne "Name" de cet onglet. Blue Prism remplace les espaces
// par des underscores, donc un Data Item "File Path" devient la variable C# `File_Path` :
//   Inputs:
//     Collection  (Collection) -> variable C# `Collection`  (System.Data.DataTable)
//     File Path   (Text)       -> variable C# `File_Path`   (string)
//     Sheet Name  (Text, opt.) -> variable C# `Sheet_Name`  (string)
//   Outputs:
//     Sheets Written (Text)    -> variable C# `Sheets_Written` (nom de la feuille ecrite)
//
// Le code n'a besoin d'AUCUNE reference d'assembly ni d'AUCUN namespace declare :
//   - Excel est pilote en COM tardif via le ProgID "Excel.Application" (il faut seulement
//     qu'Excel soit installe sur la machine, design ET Runtime Resource) ;
//   - tous les types sont ecrits en nom complet et rien ne vient de System.Core.dll
//     (donc ni LINQ ni HashSet<T> — le Code Stage ne reference pas cet assembly).
//
// A coller tel quel dans la zone de code du Code Stage, en commencant a la ligne
// `Sheets_Written = "";` — sans lignes `using`, sans methode englobante, et sans modificateur
// d'acces (`private`/`public`) sur les fonctions du bas : Blue Prism compile ce texte comme le
// corps de sa propre methode generee.

Sheets_Written = "";

if (Collection == null)
    throw new System.InvalidOperationException("La collection d'entree n'est pas initialisee.");
if (File_Path == null || File_Path.Trim().Length == 0)
    throw new System.InvalidOperationException("File Path est obligatoire.");

// Passe 1 : parcourir tout l'export pour savoir, par chemin de collection imbriquee, combien de
// creneaux reserver (colMaxCounts) et sur quelle sous-collection lire le schema (colSamples).
// Hashtable plutot que Dictionary<> : Dictionary<> vit dans System.Core.dll, pas Hashtable.
System.Collections.Hashtable colMaxCounts = new System.Collections.Hashtable();
System.Collections.Hashtable colSamples = new System.Collections.Hashtable();
ScanTable(Collection, "", colMaxCounts, colSamples);

// Passe 2 : deduire l'entete aplatie complete.
System.Collections.Generic.List<string> headerList = new System.Collections.Generic.List<string>();
BuildHeaders(Collection, "", "", colMaxCounts, colSamples, headerList);

if (headerList.Count == 0)
    throw new System.InvalidOperationException("La collection ne contient aucune colonne exportable.");
if (headerList.Count > 16384)
    throw new System.InvalidOperationException("L'aplatissement produit " + headerList.Count.ToString()
        + " colonnes, au-dela de la limite Excel de 16384. Reduisez le nombre de colonnes exportees"
        + " ou repassez sur un export en feuilles separees.");

System.Collections.Hashtable headerPos = new System.Collections.Hashtable();
for (int hi = 0; hi < headerList.Count; hi++)
    headerPos[headerList[hi]] = hi;

// Passe 3 : remplir la grille, une ligne par enregistrement parent.
int totalCols = headerList.Count;
int totalRows = Collection.Rows.Count + 1;
object[,] cellGrid = new object[totalRows, totalCols];

for (int hi = 0; hi < totalCols; hi++)
    cellGrid[0, hi] = headerList[hi];

for (int ri = 0; ri < Collection.Rows.Count; ri++)
    EmitRow(Collection.Rows[ri], "", "", cellGrid, ri + 1, headerPos, colMaxCounts);

string rootSheet = SafeSheetName(Sheet_Name);

System.Type xlType = System.Type.GetTypeFromProgID("Excel.Application");
if (xlType == null)
    throw new System.InvalidOperationException("Microsoft Excel n'est pas installe sur cette machine (ProgID 'Excel.Application' introuvable).");

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

    // Un classeur neuf peut contenir plusieurs feuilles vides selon la config d'Excel :
    // on ne garde que la premiere, qu'on renomme.
    object bookSheets = GetProp(xlBook, "Sheets");
    int bookSheetCount = System.Convert.ToInt32(GetProp(bookSheets, "Count"));
    for (int idx = bookSheetCount; idx >= 2; idx--)
    {
        object extraSheet = GetProp(bookSheets, "Item", idx);
        Invoke(extraSheet, "Delete");
        System.Runtime.InteropServices.Marshal.ReleaseComObject(extraSheet);
    }

    object mainWs = GetProp(bookSheets, "Item", 1);
    SetProp(mainWs, "Name", rootSheet);
    System.Runtime.InteropServices.Marshal.ReleaseComObject(bookSheets);

    object topLeft = GetProp(mainWs, "Cells", 1, 1);
    object bottomRight = GetProp(mainWs, "Cells", totalRows, totalCols);
    object rng = GetProp(mainWs, "Range", topLeft, bottomRight);
    SetProp(rng, "Value2", cellGrid);
    object rngCols = GetProp(rng, "Columns");
    Invoke(rngCols, "AutoFit");
    System.Runtime.InteropServices.Marshal.ReleaseComObject(rngCols);
    System.Runtime.InteropServices.Marshal.ReleaseComObject(rng);
    System.Runtime.InteropServices.Marshal.ReleaseComObject(bottomRight);
    System.Runtime.InteropServices.Marshal.ReleaseComObject(topLeft);
    System.Runtime.InteropServices.Marshal.ReleaseComObject(mainWs);

    // 51 = xlOpenXMLWorkbook (.xlsx)
    Invoke(xlBook, "SaveAs", File_Path, 51);
    Sheets_Written = rootSheet;
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

// --- Passe 1 : recensement des collections imbriquees -------------------------------------
// counts[chemin] = nombre max de lignes vues dans cette sous-collection sur tout l'export.
// samps[chemin] = une sous-collection non vide, dont on lira le schema pour l'entete.
// Le chemin ignore les numeros de creneau ("Liste Emprunteur.Adresses"), pour que tous les
// creneaux d'une meme liste partagent la meme mise en page.
void ScanTable(System.Data.DataTable tbl, string spath,
    System.Collections.Hashtable counts, System.Collections.Hashtable samps)
{
    foreach (System.Data.DataColumn dcol in tbl.Columns)
    {
        if (dcol.DataType != typeof(System.Data.DataTable))
            continue;

        string cpath = spath + dcol.ColumnName;
        foreach (System.Data.DataRow drow in tbl.Rows)
        {
            object cell = drow[dcol];
            if (!(cell is System.Data.DataTable))
                continue;

            System.Data.DataTable sub = (System.Data.DataTable)cell;

            int seen = 0;
            if (counts.Contains(cpath))
                seen = (int)counts[cpath];
            if (sub.Rows.Count > seen)
                seen = sub.Rows.Count;
            counts[cpath] = seen;

            if (!samps.Contains(cpath) && sub.Columns.Count > 0)
                samps[cpath] = sub;

            ScanTable(sub, cpath + ".", counts, samps);
        }
    }
}

// --- Passe 2 : entete aplatie --------------------------------------------------------------
void BuildHeaders(System.Data.DataTable schemaTbl, string disp, string spath,
    System.Collections.Hashtable counts, System.Collections.Hashtable samps,
    System.Collections.Generic.List<string> heads)
{
    foreach (System.Data.DataColumn dcol in schemaTbl.Columns)
    {
        if (dcol.DataType != typeof(System.Data.DataTable))
        {
            heads.Add(disp + dcol.ColumnName);
            continue;
        }

        string cpath = spath + dcol.ColumnName;
        int slots = 0;
        if (counts.Contains(cpath))
            slots = (int)counts[cpath];
        if (slots <= 0 || !samps.Contains(cpath))
            continue;

        System.Data.DataTable sample = (System.Data.DataTable)samps[cpath];
        if (slots == 1)
        {
            BuildHeaders(sample, disp + dcol.ColumnName + "-", cpath + ".", counts, samps, heads);
        }
        else
        {
            for (int slot = 1; slot <= slots; slot++)
                BuildHeaders(sample, disp + dcol.ColumnName + "-" + slot.ToString() + "-",
                    cpath + ".", counts, samps, heads);
        }
    }
}

// --- Passe 3 : valeurs ---------------------------------------------------------------------
// Reconstruit les memes noms de colonnes que BuildHeaders et place chaque valeur via headerPos.
// Un nom absent de l'entete (schema imbrique divergent) est simplement ignore.
void EmitRow(System.Data.DataRow drow, string disp, string spath,
    object[,] cells, int gridRow,
    System.Collections.Hashtable hpos, System.Collections.Hashtable counts)
{
    foreach (System.Data.DataColumn dcol in drow.Table.Columns)
    {
        if (dcol.DataType != typeof(System.Data.DataTable))
        {
            string flatName = disp + dcol.ColumnName;
            if (hpos.Contains(flatName))
                cells[gridRow, (int)hpos[flatName]] = ToCellValue(drow[dcol]);
            continue;
        }

        string cpath = spath + dcol.ColumnName;
        int slots = 0;
        if (counts.Contains(cpath))
            slots = (int)counts[cpath];
        if (slots <= 0)
            continue;

        object cell = drow[dcol];
        if (!(cell is System.Data.DataTable))
            continue;

        System.Data.DataTable sub = (System.Data.DataTable)cell;
        for (int k = 0; k < sub.Rows.Count && k < slots; k++)
        {
            string childDisp;
            if (slots == 1)
                childDisp = disp + dcol.ColumnName + "-";
            else
                childDisp = disp + dcol.ColumnName + "-" + (k + 1).ToString() + "-";

            EmitRow(sub.Rows[k], childDisp, cpath + ".", cells, gridRow, hpos, counts);
        }
    }
}

// --- Utilitaires ---------------------------------------------------------------------------

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

// Noms de feuille Excel : 31 caracteres max, pas de [ ] * ? : / \.
string SafeSheetName(string wanted)
{
    string clean = "";
    if (wanted != null)
    {
        for (int p = 0; p < wanted.Length; p++)
        {
            char ch = wanted[p];
            if (ch != '[' && ch != ']' && ch != '*' && ch != '?' && ch != ':' && ch != '/' && ch != '\\')
                clean = clean + ch;
        }
    }
    clean = clean.Trim();
    if (clean.Length == 0)
        clean = "Data";
    if (clean.Length > 31)
        clean = clean.Substring(0, 31);
    return clean;
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
