$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$narrationFolder = Join-Path $PSScriptRoot 'narration-v2'
New-Item -ItemType Directory -Path $narrationFolder -Force | Out-Null
$scenes = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'btmgpa-story.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$voice = New-Object System.Speech.Synthesis.SpeechSynthesizer
$voice.SelectVoice('Microsoft Raul')
$voice.Rate = 1
$voice.Volume = 100
for ($index = 0; $index -lt $scenes.Count; $index++) {
    $outputPath = Join-Path $narrationFolder ('scene-{0}.wav' -f $index)
    $voice.SetOutputToWaveFile($outputPath)
    $voice.Speak($scenes[$index].speech)
    $voice.SetOutputToNull()
}
$voice.Dispose()
Write-Output 'Narración española creada con voz sintética Microsoft Raul.'
