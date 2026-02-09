$outFile = "C:\Users\nateg\OneDrive\Desktop\ScuffedRDMA\scripts\mlxup_output.txt"

"=== mlxup Query ===" | Out-File $outFile
& "C:\Users\nateg\Downloads\mlxup.exe" --query 2>&1 | Out-File $outFile -Append

"`n=== mlxup Update ===" | Out-File $outFile -Append
& "C:\Users\nateg\Downloads\mlxup.exe" --update --yes 2>&1 | Out-File $outFile -Append
