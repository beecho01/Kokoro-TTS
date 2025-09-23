# --- Settings ---
$BaseUrl   = "http://192.168.0.17:8880/v1/audio/speech"
$OutDir    = $PSScriptRoot
$Format    = "mp3"
$SkipExisting = $true
$SleepMs = 150

if (!(Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }

# Localised demo text
$textByLang = @{
  "American English"      = "Hello, I’m a Kokoro voice. This is a demo.";
  "British English"       = "Hello there, I’m a Kokoro voice. This is a demo.";
  "Japanese"              = "こんにちは、私はココロの声です。これはデモです。";
  "Mandarin Chinese"      = "你好，我是 Kokoro 的声音。这是一个演示。";
  "Spanish"               = "Hola, soy una voz de Kokoro. Esta es una demostración.";
  "French"                = "Bonjour, je suis une voix Kokoro. Ceci est une démonstration.";
  "Hindi"                 = "नमस्ते, मैं कोकोरो की आवाज़ हूँ। यह एक डेमो है।";
  "Italian"               = "Ciao, sono una voce di Kokoro. Questa è una demo.";
  "Brazilian Portuguese"  = "Olá, eu sou uma voz do Kokoro. Esta é uma demonstração.";
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
foreach ($lang in $byLang.Keys) {
  $text = $textByLang[$lang]
  foreach ($id in $byLang[$lang]) {
    $outFile = Join-Path $OutDir "$id.$Format"
    if ($SkipExisting -and (Test-Path $outFile)) {
      Write-Host "Skipping existing $id"
      continue
    }

    Write-Host "Generating $id ($lang) -> $outFile"
    $body = @{
      model = "kokoro"
      input = $text
      voice = $id
      response_format = $Format
      download_format = $Format
      speed = 1
      stream = $true
      return_download_link = $false
    } | ConvertTo-Json -Compress -Depth 3

    try {
      Invoke-WebRequest -Uri $BaseUrl `
        -Method Post `
        -ContentType "application/json; charset=utf-8" `
        -Body $body `
        -OutFile $outFile
    }
    catch {
      Write-Warning "Failed: $id -> $($_.Exception.Message)"
    }
    Start-Sleep -Milliseconds $SleepMs
  }
}