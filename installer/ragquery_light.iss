; RAGQuery - Versão A (Light)
; Instalador sem modelo LLM (~50-80 MB)
; O usuário pode baixar o modelo pela interface web

#define MyAppName "RAGQuery"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "RAGQuery"
#define MyAppURL "https://github.com/lrzcalmon/RAGQuery"
#define MyAppExeName "RAGQuery.exe"

[Setup]
AppId={{E4A1F2B3-C5D6-4E7F-8A9B-0C1D2E3F4A5B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=
OutputDir=output
OutputBaseFilename=RAGQuery-{#MyAppVersion}-Light-Setup
SetupIconFile=ragquery.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes

[Languages]
Name: "portuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Aplicação PyInstaller (sem modelo LLM)
Source: "dist\RAGQuery\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "models\*.gguf"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Comment: "Consulta DDL Oracle"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; Comment: "Consulta DDL Oracle"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Iniciar {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\data"
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\models"

[Messages]
portuguese.WelcomeLabel2=Este assistente irá instalar o [name] no seu computador.%n%nVersão Light: sem modelo de IA. O download do modelo (~2.4 GB) pode ser feito pela interface do aplicativo.%n%nO sistema funciona perfeitamente sem IA para consultas estruturadas.
