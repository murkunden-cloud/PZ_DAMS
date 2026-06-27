Set WshShell = CreateObject("WScript.Shell")
strDesktop = WshShell.SpecialFolders("Desktop")
strScriptPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)

Set oShellLink = WshShell.CreateShortcut(strDesktop & "\DAMS Manager.lnk")
oShellLink.TargetPath = strScriptPath & "\Silent_Launch.vbs"
oShellLink.WindowStyle = 1
oShellLink.Description = "Launch DAMS Manager Silently"
oShellLink.WorkingDirectory = strScriptPath
' Try to use a nice icon from the system or python if possible. 
' We'll just leave default icon for vbs, or use shell32.dll icon
oShellLink.IconLocation = "shell32.dll, 137"
oShellLink.Save

WScript.Echo "Desktop shortcut 'DAMS Manager' created successfully!"
