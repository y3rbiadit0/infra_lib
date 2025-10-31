param (
    [string]$pyprojectPath = "pyproject.toml",
    [string]$versionFilePath = "src/infra_lib/cli/__version__.py",
    [ValidateSet("major", "minor", "patch")]
    [string]$versionType = "patch"
)

function Get-CurrentVersion {
    param (
        [string]$PyprojectPath
    )

    $content = Get-Content $PyprojectPath -Raw
    if ($content -match 'version\s*=\s*"(\d+)\.(\d+)\.(\d+)"') {
        return @{ 
            Major = [int]$matches[1]; 
            Minor = [int]$matches[2]; 
            Patch = [int]$matches[3]; 
            RawContent = $content 
        }
    } else {
        throw "Could not find a version in $PyprojectPath"
    }
}

function Increment-Version {
    param (
        [int]$Major,
        [int]$Minor,
        [int]$Patch,
        [ValidateSet("major", "minor", "patch")]
        [string]$VersionType
    )

    switch ($VersionType) {
        "major" {
            $Major++
            $Minor = 0
            $Patch = 0
        }
        "minor" {
            $Minor++
            $Patch = 0
        }
        "patch" {
            $Patch++
        }
    }

    return "$Major.$Minor.$Patch"
}

function Update-VersionFiles {
    param (
        [string]$NewVersion,
        [string]$PyprojectPath,
        [string]$VersionFilePath,
        [string]$PyprojectContent
    )

    $newContent = $PyprojectContent -replace 'version\s*=\s*"\d+\.\d+\.\d+"', "version = `"$NewVersion`""
    Set-Content $PyprojectPath $newContent
    Write-Host "✅ Updated $PyprojectPath to $NewVersion"

    if (Test-Path $VersionFilePath) {
        Set-Content $VersionFilePath "__version__ = `"$NewVersion`""
        Write-Host "✅ Updated $VersionFilePath to $NewVersion"
    } else {
        Write-Warning "⚠️ $VersionFilePath not found. Skipping."
    }
}

function Format-Code {
    Write-Host "🧹 Running ruff to format code..."
    ruff format .
}

function Apply-Changes {
    param (
        [string]$NewVersion,
        [string[]]$FilesToCommit
    )

    git add $FilesToCommit
    git commit -m "New Release v$NewVersion"
    git tag "v$NewVersion"
    Write-Host "✅ Committed and tagged version v$NewVersion."
}

try {
    $currentVersion = Get-CurrentVersion -PyprojectPath $pyprojectPath
    $newVersion = Increment-Version -Major $currentVersion.Major -Minor $currentVersion.Minor -Patch $currentVersion.Patch -VersionType $versionType
    Write-Host "Bumping $versionType version → $newVersion"
    
    Update-VersionFiles -NewVersion $newVersion -PyprojectPath $pyprojectPath -VersionFilePath $versionFilePath -PyprojectContent $currentVersion.RawContent
    
    $confirmation = Read-Host "Are you sure you want to commit and tag version $newVersion? (y/n)"
    if ($confirmation -eq "y") {
        Format-Code
        Apply-Changes -NewVersion $newVersion -FilesToCommit @($pyprojectPath, $versionFilePath)
    } else {
        Write-Host "Operation cancelled."
    }

    Write-Host "Done. Version bumped, files updated, and code formatted."
} catch {
    Write-Error $_
}
