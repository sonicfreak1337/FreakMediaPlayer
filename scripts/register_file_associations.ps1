param(
    [Parameter(Mandatory = $true)]
    [string]$ExecutablePath
)

$resolvedExecutable = (Resolve-Path -LiteralPath $ExecutablePath).Path
$progId = "FreakMediaPlayer.Audio"
$classes = "HKCU:\Software\Classes"
$extensions = ".aac", ".aiff", ".alac", ".flac", ".m4a", ".mp3", ".ogg", ".opus", ".wav", ".wma"

New-Item -Path "$classes\$progId\shell\open\command" -Force | Out-Null
Set-ItemProperty -Path "$classes\$progId" -Name "(Default)" -Value "Freak Media Player audio"
Set-ItemProperty -Path "$classes\$progId\shell\open\command" -Name "(Default)" -Value "`"$resolvedExecutable`" `"%1`""
foreach ($extension in $extensions) {
    New-Item -Path "$classes\$extension\OpenWithProgids" -Force | Out-Null
    New-ItemProperty -Path "$classes\$extension\OpenWithProgids" -Name $progId -Value "" -Force | Out-Null
}
Write-Host "Freak Media Player was added to Open with for supported audio files."
