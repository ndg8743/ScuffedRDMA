Write-Host "=== Running mlxup --query ===" -ForegroundColor Cyan
& "C:\Users\nateg\Downloads\mlxup.exe" --query 2>&1 | ForEach-Object { Write-Host $_ }
Write-Host "`n=== Done ===" -ForegroundColor Cyan
Read-Host "Press Enter to close"
