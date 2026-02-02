if (-not (Test-Path "office-vba-reference\.git")) {
    git submodule update --init
}

python -m scripts
python -m pip install -e .
python -m tests
if ($LASTEXITCODE -eq 0) {
    python -m build
} else {
    Write-Error "Tests failed, aborting build."
    exit 1
}
