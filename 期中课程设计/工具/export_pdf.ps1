# 可选：在安装 Microsoft Word 的 Windows 上导出 PDF，并记录实际分页。
# 运行：powershell -ExecutionPolicy Bypass -File 工具/export_pdf.ps1
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$inputFile = Join-Path $root '期中课程设计报告.docx'
$outputFile = Join-Path $root '期中课程设计报告.pdf'
$word = $null
$document = $null
$temporaryCopy = Join-Path $env:TEMP ('courseviz-' + [guid]::NewGuid().ToString() + '.docx')
try {
  Copy-Item -LiteralPath $inputFile -Destination $temporaryCopy
  $word = New-Object -ComObject Word.Application
  $word.Visible = $false
  $word.DisplayAlerts = 0
  $document = $word.Documents.OpenNoRepairDialog($temporaryCopy, $false, $true)
  $document.Repaginate()
  $pages = $document.ComputeStatistics(2)
  $document.ExportAsFixedFormat($outputFile, 17)
  [pscustomobject]@{pages=$pages;renderer='Microsoft Word';pdf=$outputFile} | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 (Join-Path $root '报告分页检查.json')
  Write-Output "PDF export complete; pages=$pages"
} finally {
  if ($document) { $document.Close(0) }
  if ($word) { $word.Quit() }
  if (Test-Path -LiteralPath $temporaryCopy) { Remove-Item -LiteralPath $temporaryCopy }
}
