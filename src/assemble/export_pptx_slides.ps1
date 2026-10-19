param(
    [string]$DeckPath,
    [string]$OutDir,
    [int]$Width = 1920,
    [int]$Height = 1080
)
$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$ppt = New-Object -ComObject PowerPoint.Application
try {
    $pres = $ppt.Presentations.Open($DeckPath, $true, $false, $true)
    $n = $pres.Slides.Count
    for ($i = 1; $i -le $n; $i++) {
        $out = Join-Path $OutDir ("slide{0:D2}.png" -f $i)
        $pres.Slides.Item($i).Export($out, "PNG", $Width, $Height)
    }
    $pres.Close()
} finally {
    $ppt.Quit()
}
