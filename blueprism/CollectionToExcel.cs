// Blue Prism Code Stage — Object Studio action "Write Collection To Excel"
//
// Wiring in Blue Prism:
//   Inputs:
//     Collection   (Collection)  -> bound to C# variable `Collection` (type System.Data.DataTable)
//     File Path    (Text)        -> bound to C# variable `FilePath`   (type string)
//     Sheet Name   (Text, optional) -> bound to C# variable `SheetName` (type string)
//   Outputs:
//     Sheets Written (Text)      -> bound to C# variable `SheetsWritten` (comma-separated list)
//
//   References needed on the Code Stage: NONE. This drives Excel through late-bound COM
//   (Type.GetTypeFromProgID + reflection), not the Microsoft.Office.Interop.Excel assembly —
//   it only needs Excel installed on the machine (design AND the Runtime Resource that will
//   run this process), since that's what registers the "Excel.Application" COM ProgID.
//
//   IMPORTANT — do NOT paste "using" lines into the code box: Blue Prism's Code Stage compiles
//   this text as the body of its own generated method, so `using` directives and access
//   modifiers (`private`/`public`) on method declarations are rejected. Instead, in the Code
//   Stage editor add these to the Namespaces list (its own separate field, not the code box):
//     System.Collections.Generic
//     System.Data
//     System.Linq
//     System.Reflection
//     System.Runtime.InteropServices
//
//   Blue Prism stores a nested Collection field internally as a System.Data.DataTable value
//   inside the parent DataTable's cell, so a column whose DataType is DataTable is a nested
//   collection field — that's the signal this code uses to decide what gets its own sheet.
//
// Paste everything below (starting at the first "if") into the Code Stage's code editor —
// no wrapping method, no "using" lines, no access modifiers on the helper methods below.

if (Collection == null)
    throw new InvalidOperationException("Input collection is not set.");
if (string.IsNullOrWhiteSpace(FilePath))
    throw new InvalidOperationException("File Path is required.");

var excelType = Type.GetTypeFromProgID("Excel.Application");
if (excelType == null)
    throw new InvalidOperationException("Microsoft Excel n'est pas installé sur cette machine (ProgID 'Excel.Application' introuvable).");

var rootSheetName = string.IsNullOrWhiteSpace(SheetName) ? "Data" : SheetName;
var usedNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
var writtenSheets = new List<string>();

object excelApp = Activator.CreateInstance(excelType);
SetProp(excelApp, "Visible", false);
SetProp(excelApp, "DisplayAlerts", false);

object workbooks = GetProp(excelApp, "Workbooks");
object workbook = Invoke(workbooks, "Add");

try
{
    WriteTable(workbook, Collection, rootSheetName, usedNames, writtenSheets, parentRowKey: null);

    // Workbooks.Add() starts with a default blank sheet — drop anything we didn't write.
    object sheets = GetProp(workbook, "Sheets");
    var sheetCount = (int)GetProp(sheets, "Count");
    for (var i = sheetCount; i >= 1; i--)
    {
        object sheet = Invoke(sheets, "Item", i);
        var name = (string)GetProp(sheet, "Name");
        if (!writtenSheets.Contains(name))
            Invoke(sheet, "Delete");
        Marshal.ReleaseComObject(sheet);
    }
    Marshal.ReleaseComObject(sheets);

    // xlOpenXMLWorkbook = 51 (.xlsx)
    Invoke(workbook, "SaveAs", FilePath, 51);
    SheetsWritten = string.Join(",", writtenSheets);
}
finally
{
    Invoke(workbook, "Close", false);
    Invoke(excelApp, "Quit");
    Marshal.ReleaseComObject(workbook);
    Marshal.ReleaseComObject(workbooks);
    Marshal.ReleaseComObject(excelApp);
    GC.Collect();
    GC.WaitForPendingFinalizers();
}

// Writes one DataTable to its own sheet, then recurses into any nested-collection columns
// so multi-level nesting each lands on its own sheet.
void WriteTable(object workbook, DataTable table, string desiredSheetName,
    HashSet<string> usedNames, List<string> writtenSheets, int? parentRowKey)
{
    var sheetName = MakeUniqueSheetName(desiredSheetName, usedNames);

    object sheets = GetProp(workbook, "Sheets");
    var sheetCount = (int)GetProp(sheets, "Count");
    object afterSheet = Invoke(sheets, "Item", sheetCount);
    object ws = Invoke(sheets, "Add", Type.Missing, afterSheet, Type.Missing, Type.Missing);
    SetProp(ws, "Name", sheetName);
    Marshal.ReleaseComObject(afterSheet);
    Marshal.ReleaseComObject(sheets);
    writtenSheets.Add(sheetName);

    var nestedColumns = table.Columns.Cast<DataColumn>()
        .Where(c => c.DataType == typeof(DataTable))
        .Select(c => c.ColumnName)
        .ToList();

    var flatColumns = table.Columns.Cast<DataColumn>()
        .Where(c => c.DataType != typeof(DataTable))
        .ToList();

    var startCol = parentRowKey.HasValue ? 2 : 1;
    var totalCols = startCol + flatColumns.Count;
    var totalRows = table.Rows.Count + 1;
    var buffer = new object[totalRows, totalCols];

    if (parentRowKey.HasValue)
        buffer[0, 0] = "ParentRowKey";
    buffer[0, startCol - 1] = "RowKey";
    for (var c = 0; c < flatColumns.Count; c++)
        buffer[0, startCol + c] = flatColumns[c].ColumnName;

    for (var r = 0; r < table.Rows.Count; r++)
    {
        var row = table.Rows[r];
        var rowKey = r + 1;
        var bufRow = r + 1;

        if (parentRowKey.HasValue)
            buffer[bufRow, 0] = parentRowKey.Value;
        buffer[bufRow, startCol - 1] = rowKey;

        for (var c = 0; c < flatColumns.Count; c++)
        {
            var value = row[flatColumns[c]];
            buffer[bufRow, startCol + c] = value is DBNull ? null : value;
        }
    }

    object cellsTopLeft = Invoke(ws, "Cells", 1, 1);
    object cellsBottomRight = Invoke(ws, "Cells", totalRows, totalCols);
    object range = GetProp(ws, "Range", cellsTopLeft, cellsBottomRight);
    SetProp(range, "Value2", buffer);
    object columns = GetProp(range, "Columns");
    Invoke(columns, "AutoFit");
    Marshal.ReleaseComObject(columns);
    Marshal.ReleaseComObject(range);
    Marshal.ReleaseComObject(cellsBottomRight);
    Marshal.ReleaseComObject(cellsTopLeft);

    for (var r = 0; r < table.Rows.Count; r++)
    {
        var row = table.Rows[r];
        var rowKey = r + 1;
        foreach (var nestedCol in nestedColumns)
        {
            if (row[nestedCol] is DataTable nestedTable)
            {
                var childSheetName = $"{sheetName}_{nestedCol}";
                WriteTable(workbook, nestedTable, childSheetName, usedNames, writtenSheets, rowKey);
            }
        }
    }

    Marshal.ReleaseComObject(ws);
}

// Excel sheet names: max 31 chars, no [ ] * ? : / \, and must be unique in the workbook.
string MakeUniqueSheetName(string desired, HashSet<string> usedNames)
{
    var invalid = new[] { '[', ']', '*', '?', ':', '/', '\\' };
    var cleaned = new string(desired.Where(ch => !invalid.Contains(ch)).ToArray());
    if (string.IsNullOrWhiteSpace(cleaned))
        cleaned = "Sheet";
    if (cleaned.Length > 31)
        cleaned = cleaned.Substring(0, 31);

    var name = cleaned;
    var suffix = 1;
    while (usedNames.Contains(name))
    {
        var suffixText = "_" + suffix++;
        var baseLength = Math.Min(cleaned.Length, 31 - suffixText.Length);
        name = cleaned.Substring(0, baseLength) + suffixText;
    }

    usedNames.Add(name);
    return name;
}

// --- Late-bound COM helpers (avoid needing the Interop.Excel assembly reference) ---

object Invoke(object target, string member, params object[] args)
{
    return target.GetType().InvokeMember(member, BindingFlags.InvokeMethod, null, target, args);
}

object GetProp(object target, string member, params object[] args)
{
    return target.GetType().InvokeMember(member, BindingFlags.GetProperty, null, target, args);
}

void SetProp(object target, string member, object value)
{
    target.GetType().InvokeMember(member, BindingFlags.SetProperty, null, target, new[] { value });
}
