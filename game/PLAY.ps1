param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$emulatorPath = if ($env:OPENMSX_EXE) { $env:OPENMSX_EXE } else { Join-Path $env:ProgramFiles 'openMSX\openmsx.exe' }
if (-not (Test-Path -LiteralPath $emulatorPath)) { throw 'Install openMSX, or set OPENMSX_EXE to openmsx.exe.' }
$sharePath = if ($env:OPENMSX_SYSTEM_DATA) { $env:OPENMSX_SYSTEM_DATA } else { Join-Path (Split-Path $emulatorPath) 'share' }
$playPath = Join-Path $PSScriptRoot 'play'
$userPath = Join-Path $playPath 'user-data'
$homePath = Join-Path $playPath 'home'
$machinePath = Join-Path $userPath 'machines'
New-Item -ItemType Directory -Force $machinePath,$homePath | Out-Null
$templatePath = Join-Path $sharePath 'machines\C-BIOS_MSX1_JP.xml'
[xml]$machine = Get-Content -LiteralPath $templatePath -Raw
$ram = $machine.SelectSingleNode('//RAM/mem')
$ram.SetAttribute('base','0x8000'); $ram.SetAttribute('size','0x8000')
$machine.SelectSingleNode('//VDP/version').InnerText = 'TMS9918A'
$machine.SelectSingleNode('//VDP/vram').InnerText = '16'
$machine.SelectSingleNode('//info/code').InnerText = 'MIKERO_MSX1_32K'
$machine.SelectSingleNode('//info/description').InnerText = 'MIKERO-ODYSSEY: MSX1, 32 KiB main RAM, 16 KiB VRAM. External C-BIOS.'
foreach ($filename in $machine.SelectNodes('//ROM/rom/filename')) {
    $biosPath = Join-Path (Join-Path $sharePath 'systemroms') $filename.InnerText
    if (-not (Test-Path -LiteralPath $biosPath)) { throw "External C-BIOS not found: $biosPath" }
    $filename.InnerText = $biosPath.Replace('\','/')
}
$machine.Save((Join-Path $machinePath 'MIKERO_MSX1_32K.xml'))
$settingsPath = Join-Path $playPath 'settings.xml'
$settingsText = @'
<!DOCTYPE settings SYSTEM "settings.dtd">
<settings><settings>
<setting id="renderer">SDLGL-PP</setting>
<setting id="throttle">true</setting>
<setting id="speed">100</setting>
<setting id="pause">false</setting>
<setting id="power">true</setting>
<setting id="master_volume">65</setting>
</settings><bindings/><shortcuts/></settings>
'@
# openMSX expects XML without a leading UTF-8 BOM.
[System.IO.File]::WriteAllText($settingsPath, $settingsText, [System.Text.UTF8Encoding]::new($false))
$env:OPENMSX_SYSTEM_DATA = $sharePath
$env:OPENMSX_USER_DATA = $userPath
$env:OPENMSX_HOME = $homePath
if ($CheckOnly) { Write-Output "Ready: ASCII16 ROM, MSX1, 32 KiB RAM, 16 KiB VRAM, external C-BIOS. Emulator: $emulatorPath"; exit 0 }
& $emulatorPath -setting $settingsPath -machine MIKERO_MSX1_32K -carta (Join-Path $PSScriptRoot 'MIKERO-ODYSSEY.rom') -romtype ASCII16
exit $LASTEXITCODE
