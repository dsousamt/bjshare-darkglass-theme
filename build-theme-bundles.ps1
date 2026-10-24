# Gera *.full.css (base + variante). Use quando @import em cadeia falhar no tracker.

$ErrorActionPreference = 'Stop'

$root = $PSScriptRoot

$basePath = Join-Path $root 'bj-zerfeus-theme.css'

if (-not (Test-Path $basePath)) {

    throw "Ficheiro base não encontrado: $basePath"

}

$base = [System.IO.File]::ReadAllText($basePath, [System.Text.UTF8Encoding]::new($false))



function Build-FullVariant {

    param(

        [Parameter(Mandatory = $true)][string]$Name

    )

    $variantPath = Join-Path $root "bj-zerfeus-theme-$Name.css"

    if (-not (Test-Path $variantPath)) {

        throw "Variante não encontrada: $variantPath"

    }

    $tail = [System.IO.File]::ReadAllText($variantPath, [System.Text.UTF8Encoding]::new($false)).TrimStart()

    # Remove todos os blocos iniciais: comentario /* */ e/ou @import (ex.: Google Fonts + base)

    while ($true) {

        $next = [regex]::Replace($tail, '^\s*/\*[\s\S]*?\*/\s*', '', 1)

        if ($next.Length -lt $tail.Length) { $tail = $next; continue }

        $next = [regex]::Replace($tail, '^\s*@import\s+url\([^)]+\)\s*;\s*', '', 1)

        if ($next.Length -lt $tail.Length) { $tail = $next; continue }

        break

    }

    $banner = "`n`n/* --- bundled: bj-zerfeus-theme.css + bj-zerfeus-theme-$Name.css (generated; run build-theme-bundles.ps1 after edits) --- */`n`n"

    # @import so pode aparecer no topo do ficheiro; a variante cyberpunk usa Rajdhani
    $fontPrefix = ''
    if ($Name -eq 'cyberpunk') {
        $fontPrefix = "@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&display=swap');`n`n"
    }

    $out = $fontPrefix + $base.TrimEnd() + $banner + $tail.TrimStart()

    $outPath = Join-Path $root "bj-zerfeus-theme-$Name.full.css"

    [System.IO.File]::WriteAllText($outPath, $out, [System.Text.UTF8Encoding]::new($false))

    Write-Host "Gerado: $outPath"

}



@(

    'light',

    'dracula',

    'sepia',

    'highcontrast',

    'oled',

    'solarized',

    'matrix',

    'win95',

    'monochrome',

    'cyberpunk'

) | ForEach-Object { Build-FullVariant -Name $_ }

