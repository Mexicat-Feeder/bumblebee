Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\rad_t\.openclaw\workspace\bumblebee\dashboard"
WshShell.Run "powershell.exe -NonInteractive -ExecutionPolicy Bypass -File ""C:\Users\rad_t\.openclaw\workspace\bumblebee\dashboard\scripts\start.ps1""", 0, True
Set WshShell = Nothing
