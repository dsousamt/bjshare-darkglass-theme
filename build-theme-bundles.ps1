# Gera bj-zerfeus-theme-<nome>.full.css (base + variante num arquivo so) para cada
# variante encontrada na pasta. Use os bundles quando o @import em cadeia falhar no tracker.

$ErrorActionPreference = 'Stop'
$utf8 = [System.Text.UTF8Encoding]::new($false)
$root = $PSScriptRoot
$baseName = 'bj-zerfeus-theme.css'
$basePath = Join-Path $root $baseName

if (-not (Test-Path $basePath)) {
    throw "Arquivo base nao encontrado: $basePath"
}
$base = [System.IO.File]::ReadAllText($basePath, $utf8).Trim()

$variants = Get-ChildItem -Path $root -Filter 'bj-zerfeus-theme-*.css' |
    Where-Object { $_.Name -notlike '*.full.css' } |
    Sort-Object Name

foreach ($variant in $variants) {
    $name = $variant.BaseName -replace '^bj-zerfeus-theme-', ''
    $body = [System.IO.File]::ReadAllText($variant.FullName, $utf8)

    # Comentario de cabecalho sai; @import do base sai; outros @import (fontes) sobem
    # para o topo do bundle, pois @import so vale antes de qualquer regra.
    $body = [regex]::Replace($body, '^\s*/\*[\s\S]*?\*/', '')
    $imports = [regex]::Matches($body, '@import\s+url\([^)]+\)\s*;') |
        ForEach-Object { $_.Value } |
        Where-Object { $_ -notmatch [regex]::Escape($baseName) }
    $body = [regex]::Replace($body, '@import\s+url\([^)]+\)\s*;\s*', '').Trim()

    $prefix = ''
    if ($imports) {
        $prefix = ($imports -join "`n") + "`n`n"
    }
    $banner = "/* --- bundle gerado: $baseName + $($variant.Name) - edite os fontes e rode build-theme-bundles.ps1 --- */"
    $out = $prefix + $base + "`n`n" + $banner + "`n`n" + $body + "`n"

    $outPath = Join-Path $root "bj-zerfeus-theme-$name.full.css"
    [System.IO.File]::WriteAllText($outPath, $out, $utf8)
    Write-Host "Gerado: $outPath"
}
