# fetch_model.ps1

# 1. Create models directory if it doesn't exist
$ModelDir = "models"
if (-not (Test-Path -Path $ModelDir)) {
    New-Item -ItemType Directory -Path $ModelDir | Out-Null
    Write-Host "Created '$ModelDir' directory." -ForegroundColor Green
}

# 2. Define the Model URL (Mistral 7B Instruct v0.2 - Quantized Q4_K_M)
# This is the standard "balanced" version (fast + smart)
$ModelUrl = "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf?download=true"
$OutputFile = "$ModelDir\mistral-7b-instruct.Q4_K_M.gguf"

# 3. Download the file
Write-Host "Downloading Mistral 7B (approx 4.37 GB)..." -ForegroundColor Cyan
Write-Host "This depends on your internet speed. Please wait." -ForegroundColor Yellow

try {
    # Uses .NET downloader for better progress bars in PowerShell
    Start-BitsTransfer -Source $ModelUrl -Destination $OutputFile
    Write-Host " Download Complete: $OutputFile" -ForegroundColor Green
}
catch {
    Write-Host " Error downloading file: $_" -ForegroundColor Red
    Write-Host "Trying fallback method..."
    try {
        Invoke-WebRequest -Uri $ModelUrl -OutFile $OutputFile
        Write-Host " Download Complete (Fallback): $OutputFile" -ForegroundColor Green
    }
    catch {
        Write-Host " Critical Failure. Please download manually from:" -ForegroundColor Red
        Write-Host "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/blob/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
    }
}