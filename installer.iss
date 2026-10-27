; Inno Setup Script for SRPCOM Download Manager
[Setup]
AppId={{9F82A4D8-6C3F-4B91-A123-SRPCOMIDM001}
AppName=SRPCOM Download Manager
AppVersion=1.0.0
AppPublisher=SRPCOM
AppPublisherURL=https://srpcom.online
AppSupportURL=https://srpcom.online
AppUpdatesURL=https://srpcom.online
DefaultDirName={autopf}\SRPCOM Download Manager
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename=SRPCOM_InnoSetup
SetupIconFile=assets\logo.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\SRPCOM Download Manager.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\SRPCOM Download Manager"; Filename: "{app}\SRPCOM Download Manager.exe"; IconFilename: "{app}\assets\logo.ico"
Name: "{autodesktop}\SRPCOM Download Manager"; Filename: "{app}\SRPCOM Download Manager.exe"; IconFilename: "{app}\assets\logo.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\SRPCOM Download Manager.exe"; Description: "{cm:LaunchProgram,SRPCOM Download Manager}"; Flags: nowait postinstall skipifsilent
