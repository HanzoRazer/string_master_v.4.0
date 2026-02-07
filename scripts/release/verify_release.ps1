# verify_release.ps1
# Verifies:
#  1) SHA256 matches *.sha256 file
#  2) cosign verifies blob using *.sigstore.json bundle
#  3) (optional) GitHub release presence via gh (best-effort)
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\verify_release.ps1 -Repo OWNER/REPO -Tag vX.Y.Z
#   powershell -ExecutionPolicy Bypass -File .\verify_release.ps1 -NoGh

param(
  [string]$Repo = "",
  [string]$Tag = "",
  [switch]$NoGh
)

$zip = Get-ChildItem -Filter "Lab_Pack_SG_*.zip" | Select-Object -First 1
if (-not $zip) { throw "No Lab_Pack_SG_*.zip found in current directory" }

$shaPath = $zip.FullName + ".sha256"
$bundlePath = $zip.FullName + ".sigstore.json"

if (-not (Test-Path $shaPath)) { throw "Missing $shaPath" }
if (-not (Test-Path $bundlePath)) { throw "Missing $bundlePath" }

Write-Host "== Files =="
Write-Host "ZIP:    $($zip.FullName)"
Write-Host "SHA:    $shaPath"
Write-Host "BUNDLE: $bundlePath"
Write-Host ""

Write-Host "== SHA256 =="
$shaLine = (Get-Content $shaPath | Select-Object -First 1).Trim()
$expected = ($shaLine -split "\s+")[0].ToLower()
$actual = (Get-FileHash $zip.FullName -Algorithm SHA256).Hash.ToLower()
if ($expected -ne $actual) { throw "SHA256 mismatch. expected=$expected actual=$actual" }
Write-Host "SHA256 OK"
Write-Host ""

Write-Host "== Cosign verify-blob =="
$cosign = Get-Command cosign -ErrorAction SilentlyContinue
if (-not $cosign) {
  throw "cosign not found in PATH. Install from: https://docs.sigstore.dev/quickstart/quickstart-cosign/"
}
& cosign verify-blob --bundle $bundlePath $zip.FullName
if ($LASTEXITCODE -ne 0) { throw "cosign verification failed" }
Write-Host ""

if (-not $NoGh) {
  $gh = Get-Command gh -ErrorAction SilentlyContinue
  if ($gh -and $Repo -ne "" -and $Tag -ne "") {
    Write-Host "== GitHub release presence (best-effort) =="
    & gh release view $Tag --repo $Repo | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "gh release view failed (check auth/repo/tag)" }
    Write-Host "OK: release exists: $Repo $Tag"
    Write-Host ""
    Write-Host "NOTE: Attestation verification is org-policy/tooling dependent."
    Write-Host "See: https://docs.github.com/actions/security-for-github-actions/using-artifact-attestations/"
  } else {
    Write-Host "== GH check skipped (missing gh or Repo/Tag) =="
  }
}

Write-Host ""
Write-Host "VERIFIED: OK"
