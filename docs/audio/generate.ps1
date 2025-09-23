# --- Settings ---
$BaseUrl        = "http://192.168.0.17:8880/v1/audio/speech"
$OutDir         = $PSScriptRoot   # saves inside docs/audio
$ResponseFormat = "wav"                     # request lossless from server
$EncodeToMp3    = $true                     # convert WAV -> MP3 locally
$Mp3BitrateKbps = 320                       # 192/256/320 recommended
$KeepWav        = $false                    # delete WAV after MP3 encode
$SkipExisting   = $false                     # skip existing output files
$SleepMs        = 150                       # pause between requests to avoid overwhelming server
$FfmpegExe      = "ffmpeg"                  # use system ffmpeg
$TimeoutSeconds = 30                        # HTTP request timeout

if (!(Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }

# Check ffmpeg availability if MP3 encoding is enabled
if ($EncodeToMp3) {
  try {
    & $FfmpegExe -version 2>$null | Out-Null
    Write-Host "✓ FFmpeg found: MP3 encoding enabled" -ForegroundColor Green
  }
  catch {
    Write-Warning "FFmpeg not found! Disabling MP3 encoding. Install FFmpeg or set EncodeToMp3 = false"
    $EncodeToMp3 = $false
  }
}

# Localised demo text
$textByLang = @{
  "American English"      = "Hello, I’m a Kokoro voice. This is a demo of what I sound like speaking.";
  "British English"       = "Hello there, I’m a Kokoro voice. This is a demo of what I sound like speaking.";
  "Japanese"              = "こんにちは、私はココロの声です。これは私の話し声のデモです。";
  "Mandarin Chinese"      = "你好，我是 Kokoro 的声音。这是一个我说话时的演示。";
  "Spanish"               = "Hola, soy una voz de Kokoro. Esta es una demostración de cómo sueno al hablar.";
  "French"                = "Bonjour, je suis une voix Kokoro. Ceci est une démonstration de ma voix en parlant.";
  "Hindi"                 = "नमस्ते, मैं कोकोरो की आवाज़ हूँ। यह मेरी बोलने की आवाज़ का डेमो है।";
  "Italian"               = "Ciao, sono una voce di Kokoro. Questa è una demo di come suono quando parlo.";
  "Brazilian Portuguese"  = "Olá, eu sou uma voz do Kokoro. Esta é uma demonstração de como eu soe falando.";
}

# Persona sets
$byLang = @{
  "American English" = @("af_heart","af_alloy","af_aoede","af_bella","af_jessica","af_kore","af_nicole","af_nova","af_river","af_sarah","af_sky",
                         "am_adam","am_echo","am_eric","am_fenrir","am_liam","am_michael","am_onyx","am_puck","am_santa")
  "British English"  = @("bf_alice","bf_emma","bf_isabella","bf_lily","bm_daniel","bm_fable","bm_george","bm_lewis")
  "Japanese"         = @("jf_alpha","jf_gongitsune","jf_nezumi","jf_tebukuro","jm_kumo")
  "Mandarin Chinese" = @("zf_xiaobei","zf_xiaoni","zf_xiaoxiao","zf_xiaoyi","zm_yunjian","zm_yunxi","zm_yunxia","zm_yunyang")
  "Spanish"          = @("ef_dora","em_alex","em_santa")
  "French"           = @("ff_siwis")
  "Hindi"            = @("hf_alpha","hf_beta","hm_omega","hm_psi")
  "Italian"          = @("if_sara","im_nicola")
  "Brazilian Portuguese" = @("pf_dora","pm_alex","pm_santa")
}

# --- Generate previews ---
$totalVoices = ($byLang.Values | ForEach-Object { $_.Count } | Measure-Object -Sum).Sum
$currentVoice = 0

foreach ($lang in $byLang.Keys) {
  $text = $textByLang[$lang]
  Write-Host "`n=== Processing $lang ($($byLang[$lang].Count) voices) ===" -ForegroundColor Cyan

  foreach ($id in $byLang[$lang]) {
    $currentVoice++
    # Determine final output file (MP3 if encoding; otherwise WAV)
    $finalExt = if ($EncodeToMp3) { "mp3" } else { $ResponseFormat }
    $finalOut = Join-Path $OutDir "$id.$finalExt"

    Write-Host "[$currentVoice/$totalVoices] Processing $id..." -NoNewline

    if ($SkipExisting -and (Test-Path $finalOut)) {
      Write-Host " SKIPPED (exists)" -ForegroundColor Yellow
      continue
    }

    $wavOut = Join-Path $OutDir "$id.$ResponseFormat"

    # Build request body
    $body = @{
      model               = "kokoro"
      input               = $text
      voice               = $id
      response_format     = $ResponseFormat
      download_format     = $ResponseFormat
      speed               = 1
      stream              = $false
      return_download_link = $false
    } | ConvertTo-Json -Compress -Depth 3

    # Request audio with timeout
    try {
      Write-Host " downloading..." -NoNewline
      Invoke-WebRequest -Uri $BaseUrl `
        -Method Post `
        -ContentType "application/json; charset=utf-8" `
        -Headers @{ Accept = "audio/wav" } `
        -Body $body `
        -OutFile $wavOut `
        -TimeoutSec $TimeoutSeconds
      Write-Host " OK" -NoNewline -ForegroundColor Green
    }
    catch {
      Write-Host " FAILED: $($_.Exception.Message)" -ForegroundColor Red
      continue
    }

    # Optionally encode WAV -> MP3
    if ($EncodeToMp3) {
      try {
        Write-Host " encoding..." -NoNewline
        & $FfmpegExe -y -hide_banner -loglevel error `
          -i $wavOut `
          -codec:a libmp3lame -b:a "$($Mp3BitrateKbps)k" `
          $finalOut 2>$null

        if (-not $KeepWav -and (Test-Path $wavOut)) {
          Remove-Item $wavOut -Force
        }
        Write-Host " MP3 OK" -ForegroundColor Green
      }
      catch {
        Write-Host " MP3 FAILED: $($_.Exception.Message)" -ForegroundColor Yellow
        if (-not (Test-Path $finalOut) -and (Test-Path $wavOut)) {
          Copy-Item $wavOut $finalOut
          Write-Host " (kept as WAV)" -ForegroundColor Yellow
        }
      }
    } else {
      Write-Host " WAV OK" -ForegroundColor Green
    }

    Start-Sleep -Milliseconds $SleepMs
  }
}

# Summary
Write-Host "`n=== Generation Complete ===" -ForegroundColor Cyan
$generatedFiles = Get-ChildItem $OutDir -Filter "*.*" | Where-Object { $_.Extension -in @('.mp3', '.wav') }
Write-Host "Generated $($generatedFiles.Count) audio files in: $OutDir" -ForegroundColor Green
if ($generatedFiles.Count -gt 0) {
  $totalSize = [math]::Round(($generatedFiles | Measure-Object -Property Length -Sum).Sum / 1MB, 2)
  Write-Host "Total size: $totalSize MB" -ForegroundColor Green
}