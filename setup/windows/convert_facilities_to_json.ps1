# PowerShell script to convert tab-separated facilities file to JSON format
# Usage: .\setup\windows\convert_facilities_to_json.ps1

$ErrorActionPreference = "Stop"

# Get script directory and project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)

# File paths
$InputFile = Join-Path $ProjectRoot "data\datasets\non-accredited-facilities"
$OutputFile = Join-Path $ProjectRoot "data\datasets\non-accredited-facilities.json"

Write-Host "Converting facilities file to JSON..." -ForegroundColor Green
Write-Host "Input: $InputFile" -ForegroundColor Cyan
Write-Host "Output: $OutputFile" -ForegroundColor Cyan

# Check if input file exists
if (-not (Test-Path $InputFile)) {
    Write-Host "ERROR: Input file not found: $InputFile" -ForegroundColor Red
    exit 1
}

# Read the file
$Lines = Get-Content $InputFile -Encoding UTF8

if ($Lines.Count -eq 0) {
    Write-Host "ERROR: Input file is empty" -ForegroundColor Red
    exit 1
}

# Parse header row
$HeaderLine = $Lines[0]
$Headers = $HeaderLine -split "`t"

Write-Host "Found $($Headers.Count) columns: $($Headers -join ', ')" -ForegroundColor Yellow

# Parse data rows
$Facilities = @()

for ($i = 1; $i -lt $Lines.Count; $i++) {
    $Line = $Lines[$i]
    
    # Skip empty lines
    if ([string]::IsNullOrWhiteSpace($Line)) {
        continue
    }
    
    # Split by tab
    $Values = $Line -split "`t"
    
    # Skip if this looks like a total row
    $Exhibitor = if ($Values.Count -gt 0) { $Values[0].Trim() } else { "" }
    if ($Exhibitor -eq "" -or $Exhibitor -eq "TOTAL" -or $Exhibitor.StartsWith("http") -or $Exhibitor.StartsWith("www.")) {
        continue
    }
    
    # Create facility object
    $Facility = @{}
    
    for ($j = 0; $j -lt $Headers.Count; $j++) {
        $Header = $Headers[$j].Trim()
        $Value = if ($j -lt $Values.Count) { $Values[$j].Trim() } else { "" }
        
        # Store value (empty strings will be preserved)
        $Facility[$Header] = $Value
    }
    
    $Facilities += $Facility
}

Write-Host "Parsed $($Facilities.Count) facilities" -ForegroundColor Green

# Convert to JSON
$JsonContent = $Facilities | ConvertTo-Json -Depth 10

# Write to output file
$JsonContent | Out-File -FilePath $OutputFile -Encoding UTF8 -NoNewline

Write-Host "Successfully created JSON file: $OutputFile" -ForegroundColor Green
Write-Host "Total facilities: $($Facilities.Count)" -ForegroundColor Green

