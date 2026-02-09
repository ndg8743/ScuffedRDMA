# Diagnostic script for ConnectX-4
Write-Host "=== Device Manager Status ===" -ForegroundColor Cyan
$devs = Get-PnpDevice | Where-Object { $_.FriendlyName -like '*Mellanox*' }
foreach ($d in $devs) {
    Write-Host "$($d.FriendlyName) - Status: $($d.Status) - Problem: $($d.Problem)"
    Write-Host "  InstanceId: $($d.InstanceId)"
}

Write-Host "`n=== Recent Mellanox Events (last 50) ===" -ForegroundColor Cyan
try {
    $events = Get-WinEvent -FilterHashtable @{LogName='System'; ProviderName='*mlx*','*Mellanox*'} -MaxEvents 50 -ErrorAction SilentlyContinue
    if ($events) {
        foreach ($e in $events) {
            Write-Host "[$($e.TimeCreated)] $($e.Message)"
        }
    } else {
        Write-Host "No Mellanox events found in System log"
    }
} catch {
    Write-Host "Could not query event log: $_"
}

Write-Host "`n=== Network Events (last 10 link changes) ===" -ForegroundColor Cyan
try {
    $events = Get-WinEvent -FilterHashtable @{LogName='System'; Id=27} -MaxEvents 10 -ErrorAction SilentlyContinue
    if ($events) {
        foreach ($e in $events) {
            Write-Host "[$($e.TimeCreated)] $($e.Message.Substring(0, [Math]::Min(200, $e.Message.Length)))"
        }
    }
} catch {
    Write-Host "No link events found"
}

Write-Host "`n=== PCIe Details ===" -ForegroundColor Cyan
foreach ($name in @("Ethernet 3", "Ethernet 4")) {
    $hw = Get-NetAdapterHardwareInfo -Name $name -ErrorAction SilentlyContinue
    if ($hw) {
        Write-Host "$name : Bus=$($hw.BusNumber) Dev=$($hw.DeviceNumber) Func=$($hw.FunctionNumber) PCIe=$($hw.PciExpressCurrentLinkWidth)x @ $($hw.PciExpressCurrentLinkSpeed)"
    }
}
