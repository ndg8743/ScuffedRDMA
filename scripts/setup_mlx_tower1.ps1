# Tower 1 ConnectX-4 Setup Script
# Run as Administrator

Write-Host "=== ConnectX-4 Setup for Tower 1 (Windows) ===" -ForegroundColor Cyan

# Step 1: Remove APIPA addresses and assign static IPs
Write-Host "`n[1] Configuring IP on Ethernet 3 (Port 1)..." -ForegroundColor Yellow
# Remove existing IPs first
Remove-NetIPAddress -InterfaceAlias "Ethernet 3" -Confirm:$false -ErrorAction SilentlyContinue
New-NetIPAddress -InterfaceAlias "Ethernet 3" -IPAddress 10.0.0.1 -PrefixLength 24 -ErrorAction Stop
Write-Host "    Assigned 10.0.0.1/24 to Ethernet 3"

# Step 2: Set Jumbo Frames
Write-Host "`n[2] Setting Jumbo Frames (MTU 9014)..." -ForegroundColor Yellow
Set-NetAdapterAdvancedProperty -Name "Ethernet 3" -RegistryKeyword "*JumboPacket" -RegistryValue "9014"
Write-Host "    Jumbo Frames set to 9014"

# Step 3: Ensure adapter is enabled
Write-Host "`n[3] Enabling adapter..." -ForegroundColor Yellow
Enable-NetAdapter -Name "Ethernet 3" -Confirm:$false -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Step 4: Check status
Write-Host "`n[4] Current status:" -ForegroundColor Yellow
$a = Get-NetAdapter -Name "Ethernet 3"
Write-Host "    Status: $($a.Status)"
Write-Host "    LinkSpeed: $($a.LinkSpeed)"
Write-Host "    Driver: $($a.DriverFileName) v$($a.DriverVersion)"

$ip = Get-NetIPAddress -InterfaceAlias "Ethernet 3" -AddressFamily IPv4 -ErrorAction SilentlyContinue
if ($ip) {
    Write-Host "    IP: $($ip.IPAddress)/$($ip.PrefixLength)"
}

$jumbo = Get-NetAdapterAdvancedProperty -Name "Ethernet 3" -RegistryKeyword "*JumboPacket"
Write-Host "    Jumbo Packet: $($jumbo.DisplayValue)"

Write-Host "`n=== Done ===" -ForegroundColor Cyan
Write-Host "If status is still 'Disconnected', install WinOF-2 driver from:" -ForegroundColor Red
Write-Host "https://network.nvidia.com/products/adapter-software/ethernet/windows/winof-2/" -ForegroundColor Red
