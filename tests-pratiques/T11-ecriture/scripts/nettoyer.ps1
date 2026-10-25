# Supprime les projets jetables, les dépôts clonés et le PDF du scratchpad de T11.
# Les sorties, les jugements et les mesures restent dans tests-pratiques\T11-ecriture\.
$s = "C:\Users\Utilisateur\AppData\Local\Temp\claude\C--Users-Utilisateur-Documents-GitHub\791fed94-a8b0-414e-8a6c-8fe967283749\scratchpad\t11"
if (Test-Path -LiteralPath $s) {
  foreach ($d in "projets", "vendor", "stage", "dl-x4", "securite") {
    $p = Join-Path $s $d
    if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Recurse -Force -Confirm:$false }
  }
}
# Dossiers vides que Claude Code crée pour chaque répertoire de travail
Get-ChildItem "$env:USERPROFILE\.claude\projects" -Directory -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -like "*scratchpad-t11*" } |
  ForEach-Object { Remove-Item -LiteralPath $_.FullName -Recurse -Force -Confirm:$false }
