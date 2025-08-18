; Modern NSIS script for Metadata Cleaner with multi-architecture support
; Version: 2.0.0

; ===============================================================================
; Configuration
; ===============================================================================

!define APPNAME "Metadata Cleaner"
!define COMPANYNAME "AntGalanin06"
!define DESCRIPTION "Privacy tool for removing metadata from files"
!define VERSIONMAJOR 1
!define VERSIONMINOR 0
!define VERSIONBUILD 1

; Auto-detect architecture
!ifdef ARM64
    !define ARCH "arm64"
    !define ARCH_DISPLAY "ARM64"
    !define PROGRAMFILES_DIR "$PROGRAMFILES64"
!else
    !define ARCH "x64"
    !define ARCH_DISPLAY "x64"
    !define PROGRAMFILES_DIR "$PROGRAMFILES64"
!endif

; ===============================================================================
; Modern UI and Settings
; ===============================================================================

!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "WinMessages.nsh"
!include "FileFunc.nsh"

; Request administrator privileges
RequestExecutionLevel admin

; Installer settings
Name "${APPNAME} ${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD} (${ARCH_DISPLAY})"
OutFile "..\..\dist\MetadataCleaner-Windows-${ARCH}.exe"
InstallDir "${PROGRAMFILES_DIR}\${COMPANYNAME}\${APPNAME}"
InstallDirRegKey HKLM "Software\${COMPANYNAME}\${APPNAME}" "InstallLocation"

; Compression
SetCompressor /SOLID lzma
SetCompressorDictSize 64

; ===============================================================================
; Interface Configuration
; ===============================================================================

!define MUI_ABORTWARNING
!define MUI_ICON "..\..\assets\icons\icon.ico"
!define MUI_UNICON "..\..\assets\icons\icon.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "..\..\assets\icons\icon.ico"
!define MUI_WELCOMEFINISHPAGE_BITMAP "..\..\assets\icons\icon.ico"

; ===============================================================================
; License Configuration
; ===============================================================================

!define MUI_LICENSEPAGE_TEXT_TOP "Please review the license terms before installing ${APPNAME}."
!define MUI_LICENSEPAGE_TEXT_BOTTOM "If you accept the terms of the agreement, click I Agree to continue. You must accept the agreement to install ${APPNAME}."

; ===============================================================================
; Pages
; ===============================================================================

; Installer pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\..\docs\LICENSE_INSTALLER.txt"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Languages
!insertmacro MUI_LANGUAGE "English"

; ===============================================================================
; Macros
; ===============================================================================

!macro VerifyUserIsAdmin
    UserInfo::GetAccountType
    Pop $0
    ${If} $0 != "admin"
        MessageBox MB_ICONSTOP "Administrator rights required!$\r$\n$\r$\nPlease run the installer as an administrator."
        SetErrorLevel 740
        Quit
    ${EndIf}
!macroend

!macro CheckAndCloseApp
    ; Check if the application is running
    FindWindow $0 "" "${APPNAME}"
    ${If} $0 != 0
        MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
            "${APPNAME} is currently running.$\r$\n$\r$\nClick OK to close it automatically, or Cancel to exit the installer." \
            IDCANCEL quit_installer
        
        ; Attempt to close gracefully
        SendMessage $0 ${WM_CLOSE} 0 0 /TIMEOUT=5000
        Sleep 2000
        
        ; Force close if still running
        FindWindow $0 "" "${APPNAME}"
        ${If} $0 != 0
            MessageBox MB_OK|MB_ICONEXCLAMATION \
                "Could not automatically close ${APPNAME}.$\r$\n$\r$\nPlease close it manually and run the installer again."
            Quit
        ${EndIf}
        Goto continue_install
        
        quit_installer:
        Quit
        
        continue_install:
    ${EndIf}
!macroend

; ===============================================================================
; Functions
; ===============================================================================

Function .onInit
    SetShellVarContext all
    !insertmacro VerifyUserIsAdmin
    !insertmacro CheckAndCloseApp
    
    ; Check if already installed
    ReadRegStr $0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "UninstallString"
    ${If} $0 != ""
        MessageBox MB_YESNO|MB_ICONQUESTION \
            "${APPNAME} is already installed.$\r$\n$\r$\nDo you want to uninstall the previous version first?" \
            IDYES uninst IDNO done
        
        uninst:
        ExecWait '$0'
        
        done:
    ${EndIf}
FunctionEnd

Function un.onInit
    SetShellVarContext all
    
    MessageBox MB_YESNO|MB_ICONQUESTION \
        "Are you sure you want to completely remove ${APPNAME} and all of its components?" \
        IDYES +2
    Abort
    
    !insertmacro VerifyUserIsAdmin
FunctionEnd

; ===============================================================================
; Installation Sections
; ===============================================================================

Section "!${APPNAME} (Required)" SecCore
    SectionIn RO
    
    SetOutPath $INSTDIR
    
    ; Copy application files
    File "..\..\dist\MetadataCleaner.exe"
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"
    
    ; Registry entries for Add/Remove Programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "UninstallString" '"$INSTDIR\uninstall.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "QuietUninstallString" '"$INSTDIR\uninstall.exe" /S'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "DisplayIcon" '"$INSTDIR\MetadataCleaner.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "Publisher" "${COMPANYNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "HelpLink" "https://github.com/AntGalanin06/Metadata_Cleaner"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "URLUpdateInfo" "https://github.com/AntGalanin06/Metadata_Cleaner/releases"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "URLInfoAbout" "https://github.com/AntGalanin06/Metadata_Cleaner"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "DisplayVersion" "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "VersionMajor" ${VERSIONMAJOR}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "VersionMinor" ${VERSIONMINOR}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "NoRepair" 1
    
    ; Calculate and write estimated size
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "EstimatedSize" "$0"
    
    ; Application registry settings
    WriteRegStr HKLM "Software\${COMPANYNAME}\${APPNAME}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\${COMPANYNAME}\${APPNAME}" "Version" "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}"
    
    ; Register file associations
    WriteRegStr HKLM "Software\Classes\.jpg\OpenWithList\MetadataCleaner.exe" "" ""
    WriteRegStr HKLM "Software\Classes\.jpeg\OpenWithList\MetadataCleaner.exe" "" ""
    WriteRegStr HKLM "Software\Classes\.png\OpenWithList\MetadataCleaner.exe" "" ""
    WriteRegStr HKLM "Software\Classes\.gif\OpenWithList\MetadataCleaner.exe" "" ""
    WriteRegStr HKLM "Software\Classes\.pdf\OpenWithList\MetadataCleaner.exe" "" ""
    WriteRegStr HKLM "Software\Classes\.docx\OpenWithList\MetadataCleaner.exe" "" ""
    WriteRegStr HKLM "Software\Classes\.xlsx\OpenWithList\MetadataCleaner.exe" "" ""
    WriteRegStr HKLM "Software\Classes\.pptx\OpenWithList\MetadataCleaner.exe" "" ""
    WriteRegStr HKLM "Software\Classes\.mp4\OpenWithList\MetadataCleaner.exe" "" ""
    WriteRegStr HKLM "Software\Classes\.mov\OpenWithList\MetadataCleaner.exe" "" ""
SectionEnd

Section "Desktop Shortcut" SecDesktop
    CreateShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\MetadataCleaner.exe" "" "$INSTDIR\MetadataCleaner.exe" 0
SectionEnd

Section "Start Menu Shortcut" SecStartMenu
    CreateDirectory "$SMPROGRAMS\${COMPANYNAME}"
    CreateShortCut "$SMPROGRAMS\${COMPANYNAME}\${APPNAME}.lnk" "$INSTDIR\MetadataCleaner.exe" "" "$INSTDIR\MetadataCleaner.exe" 0
    CreateShortCut "$SMPROGRAMS\${COMPANYNAME}\Uninstall ${APPNAME}.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0
SectionEnd

Section "Add to PATH" SecPath
    ; Add installation directory to PATH for command-line access
    ReadRegStr $0 HKLM "SYSTEM\CurrentControlSet\Control\Session Manager\Environment" "PATH"
    StrCmp $0 "" AddToPath_NTPath
    StrCpy $0 "$0;$INSTDIR"
    Goto AddToPath_NTAddPath
    AddToPath_NTPath:
    StrCpy $0 "$INSTDIR"
    AddToPath_NTAddPath:
    WriteRegExpandStr HKLM "SYSTEM\CurrentControlSet\Control\Session Manager\Environment" "PATH" $0
    SendMessage ${HWND_BROADCAST} ${WM_WININICHANGE} 0 "STR:Environment" /TIMEOUT=5000
SectionEnd

; ===============================================================================
; Section Descriptions
; ===============================================================================

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecCore} "Core application files (required)"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop} "Create a shortcut on the desktop"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecStartMenu} "Create shortcuts in the Start Menu"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecPath} "Add application to system PATH for command-line access"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; ===============================================================================
; Uninstaller Section
; ===============================================================================

Section "Uninstall"
    ; Remove files
    RMDir /r "$INSTDIR"
    
    ; Remove shortcuts
    Delete "$DESKTOP\${APPNAME}.lnk"
    Delete "$SMPROGRAMS\${COMPANYNAME}\${APPNAME}.lnk"
    Delete "$SMPROGRAMS\${COMPANYNAME}\Uninstall ${APPNAME}.lnk"
    RMDir "$SMPROGRAMS\${COMPANYNAME}"
    
    ; Remove from PATH
    ReadRegStr $0 HKLM "SYSTEM\CurrentControlSet\Control\Session Manager\Environment" "PATH"
    Push $0
    Push "$INSTDIR"
    Call un.RemoveFromPath
    Pop $0
    WriteRegExpandStr HKLM "SYSTEM\CurrentControlSet\Control\Session Manager\Environment" "PATH" $0
    SendMessage ${HWND_BROADCAST} ${WM_WININICHANGE} 0 "STR:Environment" /TIMEOUT=5000
    
    ; Remove file associations
    DeleteRegKey HKLM "Software\Classes\.jpg\OpenWithList\MetadataCleaner.exe"
    DeleteRegKey HKLM "Software\Classes\.jpeg\OpenWithList\MetadataCleaner.exe"
    DeleteRegKey HKLM "Software\Classes\.png\OpenWithList\MetadataCleaner.exe"
    DeleteRegKey HKLM "Software\Classes\.gif\OpenWithList\MetadataCleaner.exe"
    DeleteRegKey HKLM "Software\Classes\.pdf\OpenWithList\MetadataCleaner.exe"
    DeleteRegKey HKLM "Software\Classes\.docx\OpenWithList\MetadataCleaner.exe"
    DeleteRegKey HKLM "Software\Classes\.xlsx\OpenWithList\MetadataCleaner.exe"
    DeleteRegKey HKLM "Software\Classes\.pptx\OpenWithList\MetadataCleaner.exe"
    DeleteRegKey HKLM "Software\Classes\.mp4\OpenWithList\MetadataCleaner.exe"
    DeleteRegKey HKLM "Software\Classes\.mov\OpenWithList\MetadataCleaner.exe"
    
    ; Remove registry entries
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}"
    DeleteRegKey HKLM "Software\${COMPANYNAME}\${APPNAME}"
    DeleteRegKey /ifempty HKLM "Software\${COMPANYNAME}"
SectionEnd

; ===============================================================================
; Helper Functions
; ===============================================================================

Function un.RemoveFromPath
    Exch $0
    Exch
    Exch $1
    Push $2
    Push $3
    Push $4
    Push $5
    Push $6
    
    IntFmt $6 "%c" 26 ; DOS EOF
    
    System::Call 'kernel32::lstrlenA(t r1) i .r2'
    StrCpy $3 $1 $2
    StrCpy $1 $0 "" $2
    StrLen $4 "$0"
    
    loop:
        StrCpy $5 $1 $4
        StrCmp $5 $0 found
        StrCmp $1 "" done
        StrCpy $1 $1 "" 1
        Goto loop
    found:
        StrCpy $5 $1 "" $4
        StrCpy $5 $5 "" 1
        StrCpy $1 $3$5
    done:
        StrCpy $0 $1
        
    Pop $6
    Pop $5
    Pop $4
    Pop $3
    Pop $2
    Pop $1
    Exch $0
FunctionEnd