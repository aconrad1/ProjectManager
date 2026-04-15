$WshShell = New-Object -ComObject WScript.Shell
$Desktop  = [System.Environment]::GetFolderPath('Desktop')
$Shortcut = $WshShell.CreateShortcut("$Desktop\ProjectManager.lnk")

$ProjectDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Python     = "C:\Users\aconrad\AppData\Local\Programs\Python\Python313\pythonw.exe"

$Shortcut.TargetPath       = $Python
$Shortcut.Arguments         = "`"$ProjectDir\scripts\gui.py`""
$Shortcut.WorkingDirectory  = $ProjectDir
$Shortcut.Description       = "ProjectManager GUI"
$Shortcut.IconLocation      = "$ProjectDir\assets\icon.ico,0"
$Shortcut.Save()

Write-Host "Shortcut created at: $Desktop\ProjectManager.lnk"
