$progId = "FreakMediaPlayer.Audio"
$classes = "HKCU:\Software\Classes"
$extensions = ".aac", ".aiff", ".alac", ".flac", ".m4a", ".mp3", ".ogg", ".opus", ".wav", ".wma"

foreach ($extension in $extensions) {
    Remove-ItemProperty -Path "$classes\$extension\OpenWithProgids" -Name $progId -ErrorAction SilentlyContinue
}
Remove-Item -LiteralPath "$classes\$progId" -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "Freak Media Player file associations were removed."
