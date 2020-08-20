# Self-elevate the script if required
if (-Not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] 'Administrator')) {
    if ([int](Get-CimInstance -Class Win32_OperatingSystem | Select-Object -ExpandProperty BuildNumber) -ge 6000) {
        $CommandLine = "-File `"" + $MyInvocation.MyCommand.Path + "`" " + $MyInvocation.UnboundArguments
        Start-Process -FilePath PowerShell.exe -Verb Runas -ArgumentList $CommandLine
        Exit
    }
}

$dirs = @{}
$dirs.Add("C:\Users\$env:UserName\AppData\Roaming\","C:\Users\$env:UserName\Desktop\TempCopies\Roaming\")
$dirs.Add("C:\Users\$env:UserName\AppData\Local\Temp\","C:\Users\$env:UserName\Desktop\TempCopies\Local\Temp\")
$dirs.Add("C:\Windows\Temp\","C:\Users\$env:UserName\Desktop\TempCopies\W_Temp\")
$dirs.Add("C:\Windows\Prefetch\","C:\Users\$env:UserName\Desktop\TempCopies\P_Temp\")


Write-Host "Press ESC and wait for script to exit when you are done"
while ( -not ( $Host.UI.RawUI.KeyAvailable -and ($Host.UI.RawUI.ReadKey("IncludeKeyUp,NoEcho").VirtualKeyCode -eq 27 ) ) ){
    ForEach ($d in $dirs.GetEnumerator()) {try {Copy-Item $($d.Name) -Destination $($d.Value) -Recurse -ErrorAction SilentlyContinue} catch [System.UnauthorizedAccessException]{}}
}