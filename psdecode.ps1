# Small script to decode a base64 and compressed Powershell script. 
# 
# This script will reverse the compression/conversion tactic used by some malicious powershell
# This script is the opposite of psencode.ps1

Param(
    [String]$contents
)


if ([String]::IsNullOrEmpty($contents)) { Write-Error "No data provided, please pass a string as the only parameter"; exit;}
	else { 
		Write-Host ""
		Write-Host "Encoded:"
		Write-Host ""
		Write-Host $contents
		Write-Host ""
		Write-Host "Decoded:"
		Write-Host ""
		Write-Output $(New-Object IO.StreamReader ($(New-Object IO.Compression.DeflateStream($(New-Object IO.MemoryStream(,$([Convert]::FromBase64String($contents)))), [IO.Compression.CompressionMode]::Decompress)), [Text.Encoding]::ASCII)).ReadToEnd();
	}
