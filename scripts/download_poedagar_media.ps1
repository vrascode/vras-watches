#requires -Version 5.1
<#
Run from normal Windows PowerShell, outside Codex.
Python/Pillow only validate local files. Only Invoke-WebRequest uses the network.
No proxy configuration, certificate bypass or execution-policy changes.
#>
[CmdletBinding()]
param(
    [string] $ProjectRoot = (Split-Path -Parent $PSScriptRoot),
    [string] $Python,
    [ValidateRange(5, 300)] [int] $TimeoutSeconds = 45,
    [switch] $PlanOnly
)

$ErrorActionPreference = 'Stop'
$projectResolved = (Resolve-Path -LiteralPath $ProjectRoot).Path
$helper = Join-Path $PSScriptRoot 'poedagar_media.py'
if (-not $Python) {
    $venvPython = Join-Path $projectResolved '.venv\Scripts\python.exe'
    if (Test-Path -LiteralPath $venvPython) { $Python = $venvPython }
    else { $Python = (Get-Command python -ErrorAction Stop).Source }
}

function Invoke-OfflineHelper {
    param([string[]] $HelperArgs)
    $resultText = @(& $Python $helper --root $projectResolved @HelperArgs)
    if ($LASTEXITCODE -ne 0) {
        throw "Local validation failed: $($resultText -join [Environment]::NewLine)"
    }
    return (($resultText -join [Environment]::NewLine) | ConvertFrom-Json)
}

function Assert-MediaUri {
    param([Uri] $MediaUri)
    if ($MediaUri.Scheme -ne 'https' -or $MediaUri.Port -ne 443 -or
        $MediaUri.DnsSafeHost -notin @('poedagareco.com', 'cdn.shopify.com') -or
        $MediaUri.UserInfo -or $MediaUri.Fragment) {
        throw "URL is outside the allowed public HTTPS media origins: $MediaUri"
    }
}

function Test-LocalNetworkDenied {
    param([Exception] $DownloadException)
    $currentException = $DownloadException
    while ($null -ne $currentException) {
        if ($currentException -is [System.Net.Sockets.SocketException] -and
            $currentException.NativeErrorCode -eq 10013) { return $true }
        $currentException = $currentException.InnerException
    }
    return ($DownloadException.Message -match '\b10013\b')
}

function Invoke-MediaDownload {
    param([string] $Url, [string] $OutFile)
    $mediaUri = [Uri] $Url
    for ($redirectCount = 0; $redirectCount -le 5; $redirectCount++) {
        Assert-MediaUri -MediaUri $mediaUri
        try {
            # Do not combine OutFile with PassThru: affected PowerShell versions
            # can produce an empty file (Microsoft PowerShell issue #15409).
            $webParameters = @{
                Uri = $mediaUri.AbsoluteUri; OutFile = $OutFile
                UseBasicParsing = $true; MaximumRedirection = 0
                TimeoutSec = $TimeoutSeconds; ErrorAction = 'Stop'
            }
            Invoke-WebRequest @webParameters
            return
        }
        catch {
            $webResponse = $_.Exception.Response
            if ($null -eq $webResponse -or [int]$webResponse.StatusCode -notin @(301,302,303,307,308)) {
                throw
            }
            $location = [string] $webResponse.Headers['Location']
            if (-not $location) { throw 'Redirect without a Location header.' }
            $mediaUri = [Uri]::new($mediaUri, $location)
            Assert-MediaUri -MediaUri $mediaUri
        }
    }
    throw 'The media source exceeded five redirects.'
}

$plan = Invoke-OfflineHelper -HelperArgs @('plan')
Write-Host ("Identified URLs: {0}; images with recorded owner authorization: {1}" -f
    $plan.urls_identified, $plan.images_authorized)

if ($PlanOnly) {
    $plan | ConvertTo-Json -Depth 10
    return
}

$storage = $plan.storage_directory
$incoming = $plan.incoming_directory
[void] [System.IO.Directory]::CreateDirectory($incoming)
$incomingResolved = (Resolve-Path -LiteralPath $incoming).Path
$expectedStorage = [System.IO.Path]::GetFullPath($storage).TrimEnd('\') + '\'
if (-not $incomingResolved.StartsWith($expectedStorage, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Staging directory resolves outside the project media directory.'
}
$lockStream = $null
$downloadedCount = 0
$reusedCount = 0
$failedCount = 0
$skippedCount = 0
$stoppedForNetworkPolicy = $false
try {
    $lockStream = [System.IO.File]::Open(
        $plan.lock_path,
        [System.IO.FileMode]::OpenOrCreate,
        [System.IO.FileAccess]::ReadWrite,
        [System.IO.FileShare]::None)
    foreach ($entry in $plan.items) {
        if ($entry.action -eq 'skip') {
            $skippedCount++
            Write-Host "SKIP $($entry.id): no recorded commercial authorization."
            continue
        }
        $temporaryFile = $null
        try {
            if ($entry.action -eq 'error') { throw $entry.reason }
            if ($entry.action -eq 'reuse') {
                $null = Invoke-OfflineHelper -HelperArgs @('reuse', '--id', $entry.id)
                $reusedCount++
                Write-Host "REUSE $($entry.id): original hash and pixels verified."
                continue
            }
            $temporaryFile = Join-Path $incomingResolved ([Guid]::NewGuid().ToString('N') + '.part')
            Invoke-MediaDownload -Url $entry.url -OutFile $temporaryFile
            $null = Invoke-OfflineHelper -HelperArgs @('finalize', '--id', $entry.id, '--candidate', $temporaryFile)
            $downloadedCount++
            Write-Host "OK $($entry.id): $($entry.product) / $($entry.variant)"
        }
        catch {
            $failedCount++
            $downloadError = $_.Exception
            Write-Warning ("FAIL {0}: {1}" -f $entry.id, $downloadError.Message)
            try {
                $null = Invoke-OfflineHelper -HelperArgs @('failure', '--id', $entry.id, '--message', $downloadError.Message)
            }
            catch { Write-Warning "Could not save receipt: $($_.Exception.Message)" }
            if (Test-LocalNetworkDenied -DownloadException $downloadError) {
                $stoppedForNetworkPolicy = $true
                Write-Warning 'Local socket permission denied. Stopping downloads; run from normal Windows PowerShell.'
                break
            }
        }
        finally {
            if ($temporaryFile -and (Test-Path -LiteralPath $temporaryFile)) {
                Remove-Item -LiteralPath $temporaryFile -ErrorAction Stop
            }
        }
    }
}
finally {
    if ($null -ne $lockStream) { $lockStream.Dispose() }
}

$report = Invoke-OfflineHelper -HelperArgs @('report')
$report | Add-Member -NotePropertyName downloaded_this_run -NotePropertyValue $downloadedCount
$report | Add-Member -NotePropertyName reused_this_run -NotePropertyValue $reusedCount
$report | Add-Member -NotePropertyName failed_this_run -NotePropertyValue $failedCount
$report | Add-Member -NotePropertyName skipped_unauthorized -NotePropertyValue $skippedCount
$report | Add-Member -NotePropertyName stopped_for_network_policy -NotePropertyValue $stoppedForNetworkPolicy
$reportJson = $report | ConvertTo-Json -Depth 10
$runReport = Join-Path $projectResolved 'artifacts\catalogos\poedagar\powershell-download-run.json'
[System.IO.File]::WriteAllText($runReport, $reportJson, [System.Text.UTF8Encoding]::new($false))
$reportJson
if ($failedCount -gt 0 -or $report.download_pending -gt 0) {
    throw 'Some originals are still missing or invalid. See the reports and per-image receipts.'
}
