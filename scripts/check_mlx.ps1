$adapters = Get-NetAdapter | Where-Object { $_.InterfaceDescription -like '*Mellanox*' }
foreach ($a in $adapters) {
    Write-Host "=== $($a.Name) ==="
    Write-Host "Description: $($a.InterfaceDescription)"
    Write-Host "Status: $($a.Status)"
    Write-Host "LinkSpeed: $($a.LinkSpeed)"
    Write-Host "Driver: $($a.DriverFileName)"
    Write-Host "DriverVersion: $($a.DriverVersion)"
    Write-Host "DriverDate: $($a.DriverDate)"
    Write-Host "ifIndex: $($a.ifIndex)"
    Write-Host ""
}

Write-Host "=== IP Configuration ==="
foreach ($a in $adapters) {
    $ip = Get-NetIPAddress -InterfaceIndex $a.ifIndex -ErrorAction SilentlyContinue
    if ($ip) {
        foreach ($i in $ip) {
            Write-Host "$($a.Name): $($i.IPAddress)/$($i.PrefixLength)"
        }
    } else {
        Write-Host "$($a.Name): No IP assigned"
    }
}
