param(
    [Parameter(Mandatory=$false)]
    [string]$Environment = "dev"
)

function Write-Success($message) { Write-Host "✓ $message" -ForegroundColor Green }
function Write-Info($message) { Write-Host "ℹ $message" -ForegroundColor Cyan }

Write-Info "Building Docker image for $Environment environment"

# Validate Docker is installed
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker is not installed or not in PATH"
    exit 1
}

# Set tag
$timestamp = Get-Date -Format "yyyyMMddHHmmss"
$imageName = "kraftdintel"
$imageTag = "$($imageName):$timestamp"
$imageTagLatest = "$($imageName):latest"

# Build image
Write-Info "Building Docker image: $imageTag"
docker build -t $imageTag -t $imageTagLatest .

if ($LASTEXITCODE -eq 0) {
    Write-Success "Docker image built successfully"
    Write-Host ""
    Write-Host "Image Tags:"
    Write-Host "  $imageTag"
    Write-Host "  $imageTagLatest"
    Write-Host ""
    
    # Show image info
    docker images | grep $imageName
}
else {
    Write-Error "Docker build failed"
    exit 1
}
