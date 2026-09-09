// Blue Prism Code Stage — Object Studio action "Write Collection To Excel"
//
// Aplatit une collection (y compris ses collections imbriquees) dans UNE SEULE feuille Excel.
// Chaque champ d'une sous-collection devient une colonne prefixee par le nom de la colonne
// parente, et les lignes d'une sous-collection s'empilent VERS LE BAS.
//
//   Collection avec une colonne imbriquee "Emprunteur" (champs Nom, Prenom) :
//
//     No Dossier | Montant | Emprunteur-Nom | Emprunteur-Prenom
//     D-001      | 1500    | Tremblay       | Marie              <- ligne parent
//                |         | Gagnon         | Luc                <- 2e emprunteur
//                |         | Roy            | Anne               <- 3e emprunteur
//
// Les valeurs du parent ne sont ecrites qu'une fois, sur la premiere ligne de son bloc.
//
// L'imbrication est recursive : "Emprunteur-Adresses-Ville". Chaque sous-ligne reserve autant
// de lignes que ses propres enfants en occupent, sinon deux emprunteurs ayant chacun plusieurs
// adresses se chevaucheraient :
//
//     No Dossier | Emprunteur-Nom | Emprunteur-Adresses-Ville
//     D-100      | Roy            | Quebec
//                |                | Levis
//                | Gagnon         | Montreal
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
//     (donc ni LINQ, ni HashSet<T>, ni Dictionary<,> — le Code Stage ne reference pas cet
//     assembly, d'ou l'emploi de System.Collections.Hashtable).
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

// Passe 1 : retenir une sous-collection non vide par chemin imbrique, pour en lire le schema
// au moment de construire l'entete. Le chemin ("Emprunteur.Adresses") ignore la position des
// lignes, puisque toutes les sous-collections d'une meme colonne partagent leur schema.
System.Collections.Hashtable colSamples = new System.Collections.Hashtable();
ScanSamples(Collection, "", colSamples);

// Passe 2 : entete aplatie.
System.Collections.Generic.List<string> headerList = new System.Collections.Generic.List<string>();
BuildHeaders(Collection, "", "", colSamples, headerList);

if (headerList.Count == 0)
    throw new System.InvalidOperationException("La collection ne contient aucune colonne exportable.");
if (headerList.Count > 16384)
    throw new System.InvalidOperationException("L'aplatissement produit " + headerList.Count.ToString()
        + " colonnes, au-dela de la limite Excel de 16384.");

System.Collections.Hashtable headerPos = new System.Collections.Hashtable();
for (int hi = 0; hi < headerList.Count; hi++)
    headerPos[headerList[hi]] = hi;

// Passe 3 : hauteur de chaque enregistrement parent (nombre de lignes qu'il occupe).
int dataRows = 0;
for (int ri = 0; ri < Collection.Rows.Count; ri++)
    dataRows = dataRows + RowHeight(Collection.Rows[ri]);

int totalCols = headerList.Count;
int totalRows = dataRows + 1;
if (totalRows > 1048576)
    throw new System.InvalidOperationException("L'aplatissement produit " + totalRows.ToString()
        + " lignes, au-dela de la limite Excel de 1048576.");

object[,] cellGrid = new object[totalRows, totalCols];
for (int hi = 0; hi < totalCols; hi++)
    cellGrid[0, hi] = headerList[hi];

// Passe 4 : remplissage. Chaque enregistrement parent demarre sous le bloc du precedent.
int gridCursor = 1;
for (int ri = 0; ri < Collection.Rows.Count; ri++)
{
    EmitRow(Collection.Rows[ri], "", "", cellGrid, gridCursor, headerPos);
    gridCursor = gridCursor + RowHeight(Collection.Rows[ri]);
}

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

// --- Passe 1 : un echantillon de schema par chemin imbrique -------------------------------
void ScanSamples(System.Data.DataTable tbl, string spath, System.Collections.Hashtable samps)
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
            if (!samps.Contains(cpath) && sub.Columns.Count > 0)
                samps[cpath] = sub;

            ScanSamples(sub, cpath + ".", samps);
        }
    }
}

// --- Passe 2 : entete aplatie --------------------------------------------------------------
void BuildHeaders(System.Data.DataTable schemaTbl, string disp, string spath,
    System.Collections.Hashtable samps, System.Collections.Generic.List<string> heads)
{
    foreach (System.Data.DataColumn dcol in schemaTbl.Columns)
    {
        if (dcol.DataType != typeof(System.Data.DataTable))
        {
            heads.Add(disp + dcol.ColumnName);
            continue;
        }

        string cpath = spath + dcol.ColumnName;
        if (!samps.Contains(cpath))
            continue;

        System.Data.DataTable sample = (System.Data.DataTable)samps[cpath];
        BuildHeaders(sample, disp + dcol.ColumnName + "-", cpath + ".", samps, heads);
    }
}

// --- Passe 3 : hauteur d'une ligne ---------------------------------------------------------
// Une ligne occupe au moins une ligne Excel ; si elle porte des sous-collections, elle occupe
// la hauteur de la plus haute d'entre elles (chaque sous-ligne comptant sa propre hauteur).
int RowHeight(System.Data.DataRow hrow)
{
    int tallest = 1;
    foreach (System.Data.DataColumn dcol in hrow.Table.Columns)
    {
        if (dcol.DataType != typeof(System.Data.DataTable))
            continue;

        object cell = hrow[dcol];
        if (!(cell is System.Data.DataTable))
            continue;

        System.Data.DataTable sub = (System.Data.DataTable)cell;
        int stacked = 0;
        for (int k = 0; k < sub.Rows.Count; k++)
            stacked = stacked + RowHeight(sub.Rows[k]);

        if (stacked > tallest)
            tallest = stacked;
    }
    return tallest;
}

// --- Passe 4 : valeurs ---------------------------------------------------------------------
// Les champs plats vont sur gridRow ; chaque sous-ligne demarre sous la precedente, en
// reservant sa propre hauteur. Un nom absent de l'entete est ignore.
void EmitRow(System.Data.DataRow drow, string disp, string spath,
    object[,] cells, int gridRow, System.Collections.Hashtable hpos)
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

        object cell = drow[dcol];
        if (!(cell is System.Data.DataTable))
            continue;

        System.Data.DataTable sub = (System.Data.DataTable)cell;
        string childDisp = disp + dcol.ColumnName + "-";
        string childPath = spath + dcol.ColumnName + ".";

        int cursor = gridRow;
        for (int k = 0; k < sub.Rows.Count; k++)
        {
            EmitRow(sub.Rows[k], childDisp, childPath, cells, cursor, hpos);
            cursor = cursor + RowHeight(sub.Rows[k]);
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
