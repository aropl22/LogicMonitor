$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$users = @()

# Run query user
$output = & "C:\Windows\System32\query.exe" user

# Skip the header line and parse each session line
foreach ($line in $output | Select-Object -Skip 1) {
    # Split by whitespace, but keep only non-empty fields
    $parts = $line -split '\s+' | Where-Object { $_ -ne '' }

    if ($parts.Count -ge 4) {
        $username = $parts[0]
        $state = $parts[2]  # usually "Active" or "Disc"
        if ($state -eq "Active") {
            $users += $username
        }
    }
}

$users = $users | Sort-Object -Unique
$logLine = "$timestamp : $($users -join ',')"

Add-Content -Path "C:\Logs\ActiveUsers.log" -Value $logLine

