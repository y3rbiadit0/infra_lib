$pyprojectPath = "pyproject.toml"

$content = Get-Content $pyprojectPath -Raw

if ($content -match 'version\s*=\s*"(\d+)\.(\d+)\.(\d+)"') {
    $major = [int]$matches[1]
    $minor = [int]$matches[2]
    $patch = [int]$matches[3]

    $patch++
    $newVersion = "$major.$minor.$patch"
    Write-Host "Bumping version to $newVersion"
    
    # Run ruff to auto-format and fix code issues
    Write-Host "Running ruff to format code..."
    ruff format .

    $confirmation = Read-Host "Are you sure you want to commit and tag version $newVersion? (y/n)"

    if ($confirmation -eq "y") {
        $newContent = $content -replace 'version\s*=\s*"\d+\.\d+\.\d+"', "version = `"$newVersion`""
        Set-Content $pyprojectPath $newContent
        git add $pyprojectPath
        git commit -m "New Release v$newVersion"
        git tag $newVersion

        Write-Host "Committed and tagged version $newVersion."
    } else {
        Write-Host "Operation cancelled."
    }

    Write-Host "Done. Version bumped and code formatted with ruff."
} else {
    Write-Error "Could not find a version in pyproject.toml"
}
