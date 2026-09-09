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
//   Reference needed on the Code Stage: Microsoft.Office.Interop.Excel — this is the Primary
//   Interop Assembly that ships with Microsoft Excel, so nothing needs to be downloaded: if
//   Excel is installed on the machine (true wherever Blue Prism's own MS Excel VBO is used),
//   the DLL already exists on disk (typically under the GAC or the Office install folder) and
//   just needs to be added as a reference on the Code Stage.
//
//   Blue Prism stores a nested Collection field internally as a System.Data.DataTable value
//   inside the parent DataTable's cell, so a column whose DataType is DataTable is a nested
//   collection field — that's the signal this code uses to decide what gets its own sheet.
//
// Paste everything below into the Code Stage's code editor. `Main()` is the entry point Blue
// Prism calls; the other methods are ordinary helpers in the same Code Stage.

using System;
using System.Collections.Generic;
using System.Data;
using System.Linq;
using System.Runtime.InteropServices;
using Excel = Microsoft.Office.Interop.Excel;

private void Main()
{
    if (Collection == null)
        throw new InvalidOperationException("Input collection is not set.");
    if (string.IsNullOrWhiteSpace(FilePath))
        throw new InvalidOperationException("File Path is required.");

    var rootSheetName = string.IsNullOrWhiteSpace(SheetName) ? "Data" : SheetName;
    var usedNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
    var writtenSheets = new List<string>();

    var excelApp = new Excel.Application();
    excelApp.Visible = false;
    excelApp.DisplayAlerts = false;
    var workbook = excelApp.Workbooks.Add();

    try
    {
        WriteTable(workbook, Collection, rootSheetName, usedNames, writtenSheets, parentRowKey: null);

        // Workbooks.Add() starts with a default blank sheet — drop anything we didn't write.
        for (var i = workbook.Sheets.Count; i >= 1; i--)
        {
            var sheet = (Excel.Worksheet)workbook.Sheets[i];
            if (!writtenSheets.Contains(sheet.Name))
                sheet.Delete();
            else
                Marshal.ReleaseComObject(sheet);
        }

        workbook.SaveAs(FilePath, Excel.XlFileFormat.xlOpenXMLWorkbook);
        SheetsWritten = string.Join(",", writtenSheets);
    }
    finally
    {
        workbook.Close(false);
        excelApp.Quit();
        Marshal.ReleaseComObject(workbook);
        Marshal.ReleaseComObject(excelApp);
        GC.Collect();
        GC.WaitForPendingFinalizers();
    }
}

// Writes one DataTable to its own sheet, then recurses into any nested-collection columns
// so multi-level nesting each lands on its own sheet.
private void WriteTable(Excel.Workbook workbook, DataTable table, string desiredSheetName,
    HashSet<string> usedNames, List<string> writtenSheets, int? parentRowKey)
{
    var sheetName = MakeUniqueSheetName(desiredSheetName, usedNames);
    var ws = (Excel.Worksheet)workbook.Sheets.Add(After: workbook.Sheets[workbook.Sheets.Count]);
    ws.Name = sheetName;
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

    var range = ws.Range[ws.Cells[1, 1], ws.Cells[totalRows, totalCols]];
    range.Value2 = buffer;
    range.Columns.AutoFit();
    Marshal.ReleaseComObject(range);

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
private string MakeUniqueSheetName(string desired, HashSet<string> usedNames)
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
