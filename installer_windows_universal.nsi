; NSIS script for Metadata Cleaner with English-only license and multi-architecture support
!define APPNAME "Metadata Cleaner"
!define COMPANYNAME "AntGalanin06"
!define DESCRIPTION "Application for removing metadata from files"
!define VERSIONMAJOR 1
!define VERSIONMINOR 0
!define VERSIONBUILD 0

; Auto-detect architecture
!include "x64.nsh"

!if ${RUNNINGX64}
    !define ARCH "x64"
    !define ARCH_DISPLAY "x64"
!else
    !define ARCH "x86"
    !define ARCH_DISPLAY "x86"
!endif

; ARM64 support (if building on ARM64 or cross-compiling)
!ifdef ARM64
    !define ARCH "arm64"
    !define ARCH_DISPLAY "ARM64"
!endif

RequestExecutionLevel admin

; Architecture-specific install directory
!if "${ARCH}" == "x64"
    InstallDir "$PROGRAMFILES64\${COMPANYNAME}\${APPNAME}"
!else if "${ARCH}" == "arm64"
    InstallDir "$PROGRAMFILES64\${COMPANYNAME}\${APPNAME}"
!else
    InstallDir "$PROGRAMFILES\${COMPANYNAME}\${APPNAME}"
!endif

Name "${APPNAME} (${ARCH_DISPLAY})"
Icon "assets\icons\icon.ico"
outFile "MetadataCleaner-Windows-${ARCH}.exe"

!include LogicLib.nsh
!include WinMessages.nsh

; English-only license file
LicenseData "docs\LICENSE_INSTALLER.txt"

; Installer pages
page license
page components  
page directory
page instfiles

!macro VerifyUserIsAdmin
UserInfo::GetAccountType
pop $0
${If} $0 != "admin"
    messageBox mb_iconstop "Administrator rights required!"
    setErrorLevel 740
    quit
${EndIf}
!macroend

function .onInit
    setShellVarContext all
    !insertmacro VerifyUserIsAdmin
functionEnd

section "install"
    setOutPath $INSTDIR
    
    ; Копируем все файлы приложения
    file /r "dist\MetadataCleaner\*"
    
    ; Создаем ярлык в меню Пуск
    createDirectory "$SMPROGRAMS\${COMPANYNAME}"
    createShortCut "$SMPROGRAMS\${COMPANYNAME}\${APPNAME}.lnk" "$INSTDIR\MetadataCleaner.exe" "" "$INSTDIR\MetadataCleaner.exe"
    
    ; Создаем ярлык на рабочем столе
    createShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\MetadataCleaner.exe" "" "$INSTDIR\MetadataCleaner.exe"
    
    ; Записываем информацию о деинсталляции
    writeUninstaller "$INSTDIR\uninstall.exe"
    
    ; Добавляем запись в "Установка и удаление программ"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "QuietUninstallString" "$\"$INSTDIR\uninstall.exe$\" /S"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "InstallLocation" "$\"$INSTDIR$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "DisplayIcon" "$\"$INSTDIR\MetadataCleaner.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "Publisher" "${COMPANYNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "HelpLink" "https://github.com/AntGalanin06/Metadata_Cleaner"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "URLUpdateInfo" "https://github.com/AntGalanin06/Metadata_Cleaner/releases"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "URLInfoAbout" "https://github.com/AntGalanin06/Metadata_Cleaner"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "DisplayVersion" "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "VersionMajor" ${VERSIONMAJOR}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "VersionMinor" ${VERSIONMINOR}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "NoRepair" 1
sectionEnd

function un.onInit
    SetShellVarContext all
    
    MessageBox MB_OKCANCEL "Remove ${APPNAME} and all of its components?" IDOK next
        Abort
    next:
    !insertmacro VerifyUserIsAdmin
functionEnd

section "uninstall"
    ; Удаляем файлы
    rmDir /r "$INSTDIR"
    
    ; Удаляем ярлыки
    delete "$SMPROGRAMS\${COMPANYNAME}\${APPNAME}.lnk"
    rmDir "$SMPROGRAMS\${COMPANYNAME}"
    delete "$DESKTOP\${APPNAME}.lnk"
    
    ; Удаляем запись из реестра
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}"
sectionEnd 