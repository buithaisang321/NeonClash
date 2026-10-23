; ============================================================
;  NEON CLASH - script cai dat Windows (Inno Setup)
;  Build: python tools/make_installer.py
; ============================================================

#define MyAppName "NEON CLASH"
#ifndef APP_VERSION
#define APP_VERSION "0.0.0"
#endif
#define MyAppExeName "NeonClash.exe"

[Setup]
AppId={{7C1A2F3E-5D4B-4E8A-9C6F-2B5D8E0A1F34}}
AppName={#MyAppName}
AppVersion={#APP_VERSION}
AppPublisher=NEON CLASH
DefaultDirName={localappdata}\Programs\NeonClash
DefaultGroupName={#MyAppName}
; cai per-user, khong can quyen admin
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=NeonClash-Setup
SetupIconFile=..\build\icon.ico
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\dist\NeonClash.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Shortcut Start Menu -> tim duoc bang Windows Search (Win+S)
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Gỡ cài đặt {#MyAppName}"; Filename: "{uninstallexe}"
; Shortcut Desktop
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Tạo shortcut ngoài Desktop"; GroupDescription: "Shortcut:"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Chơi NEON CLASH ngay"; Flags: nowait postinstall skipifsilent
; tu xoa file setup sau khi cai xong (cho 2s de setup thoat roi moi del)
Filename: "{cmd}"; Parameters: "/C ping -n 3 127.0.0.1 > nul & del ""{srcexe}"""; Flags: runhidden nowait

[UninstallDelete]
; don du lieu cache code update khi go cai dat (giu profile nguoi choi)
Type: filesandordirs; Name: "{localappdata}\NeonClash\app"
