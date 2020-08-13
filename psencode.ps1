# Small script to decode a base64 and compressed Powershell script. 
# To convert a file, call me like: .\psencode.ps1 -file C:\dir\script.ps1
# To convert a command/string, call me like: .\psencode.ps1 -command "Write-Host 'Hello World'"
# 
# This is a common tactic in malicious powershell scripts.  To reverse this from the compressed base64, use script 'psdecode.ps1'

[CmdletBinding()]
Param
(
    # Script file to compress.
    [Parameter(Mandatory=$true,
              ValueFromPipeline=$true,
              ParameterSetName="file",
              Position=0)]
    [ValidateScript({Test-Path $_})]
    $File,

    # Command to Encode
    [Parameter(Mandatory=$true,
               ValueFromPipelineByPropertyName=$true,
               ParameterSetName="command",
               Position=0)]
    [String]$Command
)

# Get contents of Script
switch ($PsCmdlet.ParameterSetName)
{
    "command" {$contents = $Command}
    "file" {$contents =  [system.io.file]::ReadAllText($File)}
}

# Compress Script
$ms = New-Object IO.MemoryStream
$action = [IO.Compression.CompressionMode]::Compress
$cs = New-Object IO.Compression.DeflateStream ($ms,$action)
$sw = New-Object IO.StreamWriter ($cs, [Text.Encoding]::ASCII)
$contents | ForEach-Object {$sw.WriteLine($_)}
$sw.Close()

# Base64 encode stream
$code = [Convert]::ToBase64String($ms.ToArray())

$command = "Invoke-Expression `$(New-Object IO.StreamReader (" +
"`$(New-Object IO.Compression.DeflateStream (" +
"`$(New-Object IO.MemoryStream (,"+
"`$([Convert]::FromBase64String('$code')))), " +
"[IO.Compression.CompressionMode]::Decompress)),"+
" [Text.Encoding]::ASCII)).ReadToEnd();" 

# If to long tell the user
if ($command.Length -gt 8100)
{
    Write-Warning "Compresses Script may be to long to run via -EncodedCommand of Powershell.exe"
}

Write-Output $command