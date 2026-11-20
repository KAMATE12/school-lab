param([string]$Results = ("results/lab2_windows_" + (Get-Date -Format "yyyyMMdd-HHmmss")))
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$python = Join-Path $PSScriptRoot ".venv/Scripts/python.exe"
if (-not (Test-Path $python)) { throw "Environnement .venv introuvable." }
if (Test-Path $Results) { throw "Le dossier de resultats existe deja; choisir un nouveau nom." }
New-Item -ItemType Directory -Path $Results | Out-Null
$Results = (Resolve-Path $Results).Path
$previousHashSeed = $env:PYTHONHASHSEED
$previousUtf8 = $env:PYTHONUTF8
$env:PYTHONHASHSEED = "0"
$env:PYTHONUTF8 = "1"
try {
    # RU: Устанавливаем исходники и проверяем все контракты.
    # EN: Install source changes and verify all contracts.
    & $python -m pip install .
    if ($LASTEXITCODE -ne 0) { throw "Installation echouee." }
    # RU: Сохраняем журнал тестов; stderr unittest не означает ошибку теста.
    # EN: Save the test log; unittest stderr output alone does not mean failure.
    $testLog = Join-Path $Results "tests.txt"
    $testErr = Join-Path $Results "tests_stderr.txt"
    $process = Start-Process -FilePath $python -ArgumentList @("-m", "unittest", "discover", "-v") -Wait -PassThru -NoNewWindow -RedirectStandardOutput $testLog -RedirectStandardError $testErr
    Get-Content $testErr
    if ($process.ExitCode -ne 0) { throw "Tests echoues. Voir tests_stderr.txt." }
    # RU: Фиксируем пороги до запуска отложенной оценки.
    # EN: Freeze thresholds before running held-out evaluation.
    $policy = Join-Path $Results "frozen_policy.json"
    & $python -m school_lab.quality_experiment tune --policy $policy
    if ($LASTEXITCODE -ne 0) { throw "Reglage echoue." }
    & $python -m school_lab.quality_experiment evaluate --policy $policy --output (Join-Path $Results "evaluation.json")
    if ($LASTEXITCODE -ne 0) { throw "Evaluation echouee." }
    # RU: Повторяем измерения без конкурентного выполнения.
    # EN: Repeat measurements without concurrent execution.
    & $python benchmark_lab2.py --output (Join-Path $Results "performance")
    if ($LASTEXITCODE -ne 0) { throw "Mesures echouees." }
    & $python write_lab2_report.py --results $Results --output (Join-Path $Results "REPORT_LAB2_RU.md")
    if ($LASTEXITCODE -ne 0) { throw "Creation du rapport echouee." }
    git rev-parse HEAD | Out-File (Join-Path $Results "base_commit.txt") -Encoding utf8
    git status --short | Out-File (Join-Path $Results "working_tree.txt") -Encoding utf8
    Write-Host "Etape B executee. Resultats: $Results"
} finally {
    $env:PYTHONHASHSEED = $previousHashSeed
    $env:PYTHONUTF8 = $previousUtf8
}
