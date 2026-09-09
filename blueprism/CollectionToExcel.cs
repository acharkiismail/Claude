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
//   References needed on the Code Stage: EPPlus.dll (NuGet package "EPPlus", add the DLL
//   under System Manager > References, or drop it next to the release and reference it there).
//   Blue Prism stores a nested Collection field internally as a System.Data.DataTable value
//   inside the parent DataTable's cell, so a column whose DataType is DataTable is a nested
//   collection field — that's the signal this code uses to decide what gets its own sheet.
//
// Paste everything below into the Code Stage's code editor. `Main()` is the entry point Blue
// Prism calls; the other methods are ordinary helpers in the same Code Stage.

using System;
using System.Collections.Generic;
using System.Data;
using System.IO;
using System.Linq;
using OfficeOpenXml;

private void Main()
{
    if (Collection == null)
        throw new InvalidOperationException("Input collection is not set.");
    if (string.IsNullOrWhiteSpace(FilePath))
        throw new InvalidOperationException("File Path is required.");

    ExcelPackage.LicenseContext = LicenseContext.NonCommercial;

    var rootSheetName = string.IsNullOrWhiteSpace(SheetName) ? "Data" : SheetName;
    var usedNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
    var writtenSheets = new List<string>();

    var file = new FileInfo(FilePath);
    using (var package = new ExcelPackage(file))
    {
        WriteTable(package, Collection, rootSheetName, usedNames, writtenSheets, parentRowKey: null);
        package.Save();
    }

    SheetsWritten = string.Join(",", writtenSheets);
}

// Writes one DataTable to its own sheet, then recurses into any nested-collection columns
// so multi-level nesting each lands on its own sheet.
private void WriteTable(ExcelPackage package, DataTable table, string desiredSheetName,
    HashSet<string> usedNames, List<string> writtenSheets, int? parentRowKey)
{
    var sheetName = MakeUniqueSheetName(desiredSheetName, usedNames);
    var ws = package.Workbook.Worksheets.Add(sheetName);
    writtenSheets.Add(sheetName);

    var nestedColumns = table.Columns.Cast<DataColumn>()
        .Where(c => c.DataType == typeof(DataTable))
        .Select(c => c.ColumnName)
        .ToList();

    var flatColumns = table.Columns.Cast<DataColumn>()
        .Where(c => c.DataType != typeof(DataTable))
        .ToList();

    var startCol = 1;
    if (parentRowKey.HasValue)
    {
        ws.Cells[1, 1].Value = "ParentRowKey";
        startCol = 2;
    }
    ws.Cells[1, startCol].Value = "RowKey";
    for (var c = 0; c < flatColumns.Count; c++)
        ws.Cells[1, startCol + 1 + c].Value = flatColumns[c].ColumnName;

    for (var r = 0; r < table.Rows.Count; r++)
    {
        var row = table.Rows[r];
        var rowKey = r + 1;
        var excelRow = r + 2;

        if (parentRowKey.HasValue)
            ws.Cells[excelRow, 1].Value = parentRowKey.Value;
        ws.Cells[excelRow, startCol].Value = rowKey;

        for (var c = 0; c < flatColumns.Count; c++)
        {
            var value = row[flatColumns[c]];
            ws.Cells[excelRow, startCol + 1 + c].Value = value is DBNull ? null : value;
        }

        foreach (var nestedCol in nestedColumns)
        {
            if (row[nestedCol] is DataTable nestedTable)
            {
                var childSheetName = $"{sheetName}_{nestedCol}";
                WriteTable(package, nestedTable, childSheetName, usedNames, writtenSheets, rowKey);
            }
        }
    }

    if (ws.Dimension != null)
        ws.Cells[ws.Dimension.Address].AutoFitColumns();
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
