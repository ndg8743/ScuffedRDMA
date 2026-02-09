# Query first, then update firmware
Write-Host "=== mlxup Query ===" -ForegroundColor Cyan
$queryOutput = & "C:\Users\nateg\Downloads\mlxup.exe" --query 2>&1
$queryOutput | ForEach-Object { Write-Host $_ }

Write-Host "`n=== mlxup Update ===" -ForegroundColor Yellow
Write-Host "Attempting firmware update..." -ForegroundColor Yellow
$updateOutput = & "C:\Users\nateg\Downloads\mlxup.exe" --update --yes 2>&1
$updateOutput | ForEach-Object { Write-Host $_ }

# Save output to file for reference
$allOutput = "=== Query ===`r`n" + ($queryOutput -join "`r`n") + "`r`n`r`n=== Update ===`r`n" + ($updateOutput -join "`r`n")
$allOutput | Out-File "C:\Users\nateg\OneDrive\Desktop\ScuffedRDMA\scripts\mlxup_output.txt"
Write-Host "`nOutput saved to scripts\mlxup_output.txt" -ForegroundColor Green

Read-Host "Press Enter to close"
