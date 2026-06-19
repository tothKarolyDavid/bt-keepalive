; Inno Setup script: compile after build.ps1 produces dist\BTKeepAlive.exe
#define MyAppName "BT KeepAlive"
; Default when not passed on the command line; keep in sync with pyproject.toml
#ifndef MyAppVersion
#define MyAppVersion "1.4.3"
#endif
#define MyAppPublisher "BT KeepAlive"
#define MyAppExeName "BTKeepAlive.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={localappdata}\Programs\BTKeepAlive
DefaultGroupName={#MyAppName}
OutputDir=..\dist
OutputBaseFilename=BTKeepAlive-setup
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startup

[Tasks]
Name: startup; Description: "Launch BT KeepAlive at Windows startup"; GroupDescription: "Additional tasks:"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
