$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$users = @()

# RemoteInteractive = RDP/Horizon sessions
$sessions = Get-CimInstance Win32_LogonSession | Where-Object { $_.LogonType -eq 10 }

foreach ($session in $sessions) {
    $linkedUsers = Get-CimAssociatedInstance -InputObject $session -ResultClassName Win32_Account
    foreach ($u in $linkedUsers) {
        $users += "$($u.Domain)\$($u.Name)"
    }
}

$users = $users | Sort-Object -Unique
$logLine = "$timestamp : $($users -join ',')"
Add-Content -Path "C:\Logs\ActiveUsers.log" -Value $logLine
