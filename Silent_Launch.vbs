Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
' Run Launch_DAMS.bat completely hidden (0)
WshShell.Run chr(34) & "Launch_DAMS.bat" & chr(34), 0
Set WshShell = Nothing
