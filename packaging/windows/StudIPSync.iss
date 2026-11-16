#define MyAppName "StudIPSync"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "StudIPSync"
#define MyAppExeName "StudIPSync.exe"

[Setup]
AppId={{1F659F15-98A9-45E4-A38B-57C943535C6E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputBaseFilename={#MyAppName}-Setup-{#MyAppVersion}
SetupIconFile={#SourcePath}\..\..\assets\studipsync.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "Desktopverknüpfung erstellen"; GroupDescription: "Zusätzliche Symbole:"; Flags: unchecked

[Files]
Source: "{#SourcePath}\..\..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{#MyAppName} starten"; Flags: postinstall nowait skipifsilent

[UninstallRun]
Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoProfile -NonInteractive -ExecutionPolicy Bypass -Command ""$task = Get-ScheduledTask -TaskName 'StudIPSync Daily' -ErrorAction SilentlyContinue; if ($task) { Unregister-ScheduledTask -TaskName 'StudIPSync Daily' -Confirm:$false }"""; Flags: runhidden waituntilterminated
