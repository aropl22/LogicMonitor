$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# Run query user via cmd
$users = cmd /c "query user" | ForEach-Object {
    $parts = ($_ -split '\s+')
    if ($parts.Count -ge 3 -and $parts[2] -eq 'Active') { $parts[0] }
}

$users = $users | Sort-Object -Unique
$logLine = "$timestamp : $($users -join ',')"
Add-Content -Path "C:\Logs\ActiveUsers.log" -Value $logLine
