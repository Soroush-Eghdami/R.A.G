param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("chat", "embedding")]
    [string]$Mode,
    [string]$ModelDirectory = "C:\Users\sorou\.lmstudio\models\lmstudio-community",
    [string]$Server = "llama-server",
    [string]$HostAddress = "127.0.0.1",
    [string]$Device = "Vulkan0",
    [int]$GpuLayers = 99,
    [int]$ContextSize = 0
)

$ErrorActionPreference = "Stop"

if ($ContextSize -eq 0) {
    $ContextSize = 8192
    $envFile = Join-Path (Split-Path $PSScriptRoot -Parent) ".env"
    if (Test-Path -LiteralPath $envFile -PathType Leaf) {
        $setting = Select-String -Path $envFile -Pattern '^\s*LLAMA_CPP_CONTEXT_SIZE\s*=\s*(\d+)\s*$' |
            Select-Object -First 1
        if ($setting) {
            $ContextSize = [int]$setting.Matches[0].Groups[1].Value
        }
    }
}
if ($ContextSize -lt 512) {
    throw "LLAMA_CPP_CONTEXT_SIZE must be at least 512."
}

if ($Mode -eq "chat") {
    $modelPath = Join-Path $ModelDirectory "Qwen3.5-9B-GGUF\Qwen3.5-9B-Q4_K_M.gguf"
    $alias = "Qwen3.5-9B"
    $port = 8082
} else {
    $modelPath = Join-Path $ModelDirectory "nomic-embed-text-v1.5-GGUF\nomic-embed-text-v1.5.Q4_K_M.gguf"
    $alias = "nomic-embed-text-v1.5"
    $port = 8083
}

if (-not (Test-Path -LiteralPath $modelPath -PathType Leaf)) {
    throw "Model file not found: $modelPath"
}

$arguments = @(
    "--model", $modelPath,
    "--alias", $alias,
    "--host", $HostAddress,
    "--port", "$port",
    "--device", $Device,
    "--n-gpu-layers", "$GpuLayers",
    "--ctx-size", "$ContextSize"
)

if ($Mode -eq "embedding") {
    $arguments += @("--embedding", "--pooling", "mean")
}

Write-Host "Starting llama.cpp $Mode server for $alias on http://${HostAddress}:$port"
& $Server @arguments
exit $LASTEXITCODE
