$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$users = @()

# Run query user and skip header
$output = & "C:\Windows\System32\query.exe" user | Select-Object -Skip 1

foreach ($line in $output) {
    if ($line -match "^\s*(\S+).*\s+(Active|Disc)\s+") {
        $username = $matches[1]
        $state    = $matches[2]
        if ($state -eq "Active") {
            $users += $username
        }
    }
}

$users = $users | Sort-Object -Unique
$logLine = "$timestamp : $($users -join ',')"
Add-Content -Path "C:\Logs\ActiveUsers.log" -Value $logLine

