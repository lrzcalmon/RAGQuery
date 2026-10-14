; RAGQuery - Versão C (Full)
; Instalador completo com modelo LLM (~2.8 GB)
; Zero configuração necessária

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
OutputBaseFilename=RAGQuery-{#MyAppVersion}-Full-Setup
SetupIconFile=ragquery.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DiskSpanning=yes
SlicesPerDisk=1
DiskSliceSize=2100000000
DisableProgramGroupPage=yes

[Languages]
Name: "portuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Aplicação PyInstaller completa (COM modelo LLM)
Source: "dist\RAGQuery\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Comment: "Consulta DDL Oracle"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; Comment: "Consulta DDL Oracle"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Iniciar {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\data"
Type: filesandordirs; Name: "{app}\logs"

[Messages]
portuguese.WelcomeLabel2=Este assistente irá instalar o [name] no seu computador.%n%nVersão Completa: inclui modelo de IA Phi-3-mini para classificação avançada de perguntas.%n%nNenhuma configuração adicional necessária.
