# Log file location
$LogFile = "C:\Logs\ActiveUsers.log"

# Get timestamp
$TimeStamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# Query WMI for console user
$UserInfo = Get-CimInstance Win32_ComputerSystem

# Collect usernames
$Users = @()
foreach ($u in $UserInfo) {
    $username = $u.UserName
    if ([string]::IsNullOrEmpty($username)) {
        $username = "No user logged in"
    }
    $Users += $username
}

# Prepare log line
$LogLine = "$TimeStamp : $($Users -join ',')"

# Write to log
Add-Content -Path $LogFile -Value $LogLine
