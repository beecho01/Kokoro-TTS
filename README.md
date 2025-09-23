<div id="top">
  <p align="center">
    <img src="https://raw.githubusercontent.com/beecho01/Kokoro-TTS/refs/heads/main/docs/images/Kokoro_Header.png" width="600" alt="Kokoro TTS Header">
  </p>
</div>

<div>
  <p align="center">
    <img src="https://img.shields.io/github/languages/top/beecho01/Kokoro-TTS?style=for-the-badge&color=FFFFFF">
    <img src="https://img.shields.io/github/languages/code-size/beecho01/Kokoro-TTS?style=for-the-badge&color=FFFFFF">
    <a href="http://creativecommons.org/licenses/by-nc-sa/4.0/"><img src="https://img.shields.io/badge/license-CC--BY--NC--SA--4.0-8257e6?style=for-the-badge&logoColor=white&label=License&color=FFFFFF"></a>
  </p>
 <br>
</div>

---

<p align="center">
  <em>
    A <a href="https://www.home-assistant.io/">Home Assistant</a> custom integration for connecting to <a href="https://github.com/remsky/Kokoro-FastAPI">Kokoro FastAPI</a>, enabling high-quality local Text-to-Speech.  
    Easily send TTS audio to your speakers or media players directly from Home Assistant.
  </em>
</p>

<p align="center">
  🎧 <strong>Listen to a preview: </strong><a href="https://beecho01.github.io/Kokoro-TTS/docs/audio/af_heart.mp3">▶ Play</a>

---

## ✨ Features

- 🔊 Convert text to speech using Kokoro FastAPI  
- ⚡ Low-latency responses for near real-time playback  
- 🎙️ Voice selection with per-call overrides  
- 🔧 Configurable server URL and parameters  
- 🏠 Works with any Home Assistant `media_player` entity  

---

## 📦 Installation

### HACS (recommended)

1. Go to `HACS` → `Integrations` → `Custom repositories`.  
2. Add this repository: `https://github.com/beecho01/Kokoro-TTS` with category `Integration`.
3. Either search for `Kokoro-TTS` in HACS or tap the below button:
   [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=beecho01&repository=material-symbols)
4. Tap `Download` and then `Install`.
5. Then tap next setup quick-link below to complete the setup configuration:
    [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=material_symbols)
6. Configure the Kokoro TTS configuration as desired.
7. Restart Home Assistant.

### Manual

1. Download the latest release from [Releases](../../releases).  
2. Copy the folder `custom_components/kokoro_tts` into your Home Assistant `custom_components` directory.  
3. Restart Home Assistant.
4. Go to `Settings` → `Devices & services`.
5. Click the `Add Configuration` button.
6. Search for `Kokoro TTS` and select it.
7. Configure the Kokoro TTS configuration as desired.
8. Restart Home Assistant.

---

## ⚙️ Configuration

Work-in-progress

---

## ▶️ Usage

Work-in-progress

| Language             | Sex | Name      | Preview | Persona Code |
|----------------------|-----|-----------|---------|--------------|
| American English 🇺🇸 | Female | Heart     | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/af_heart.mp3) | af_heart |
| American English 🇺🇸 | Female | Alloy     | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/af_alloy.mp3) | af_alloy |
| American English 🇺🇸 | Female | Aoede     | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/af_aoede.mp3) | af_aoede |
| American English 🇺🇸 | Female | Bella     | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/af_bella.mp3) | af_bella |
| American English 🇺🇸 | Female | Jessica   | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/af_jessica.mp3) | af_jessica |
| American English 🇺🇸 | Female | Kore      | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/af_kore.mp3) | af_kore |
| American English 🇺🇸 | Female | Nicole    | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/af_nicole.mp3) | af_nicole |
| American English 🇺🇸 | Female | Nova      | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/af_nova.mp3) | af_nova |
| American English 🇺🇸 | Female | River     | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/af_river.mp3) | af_river |
| American English 🇺🇸 | Female | Sarah     | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/af_sarah.mp3) | af_sarah |
| American English 🇺🇸 | Female | Sky       | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/af_sky.mp3) | af_sky |
| American English 🇺🇸 | Male   | Adam      | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/am_adam.mp3) | am_adam |
| American English 🇺🇸 | Male   | Echo      | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/am_echo.mp3) | am_echo |
| American English 🇺🇸 | Male   | Eric      | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/am_eric.mp3) | am_eric |
| American English 🇺🇸 | Male   | Fenrir    | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/am_fenrir.mp3) | am_fenrir |
| American English 🇺🇸 | Male   | Liam      | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/am_liam.mp3) | am_liam |
| American English 🇺🇸 | Male   | Michael   | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/am_michael.mp3) | am_michael |
| American English 🇺🇸 | Male   | Onyx      | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/am_onyx.mp3) | am_onyx |
| American English 🇺🇸 | Male   | Puck      | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/am_puck.mp3) | am_puck |
| American English 🇺🇸 | Male   | Santa     | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/am_santa.mp3) | am_santa |
| British English 🇬🇧  | Female | Alice     | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/bf_alice.mp3) | bf_alice |
| British English 🇬🇧  | Female | Emma      | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/bf_emma.mp3) | bf_emma |
| British English 🇬🇧  | Female | Isabella  | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/bf_isabella.mp3) | bf_isabella |
| British English 🇬🇧  | Female | Lily      | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/bf_lily.mp3) | bf_lily |
| British English 🇬🇧  | Male   | Daniel    | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/bm_daniel.mp3) | bm_daniel |
| British English 🇬🇧  | Male   | Fable     | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/bm_fable.mp3) | bm_fable |
| British English 🇬🇧  | Male   | George    | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/bm_george.mp3) | bm_george |
| British English 🇬🇧  | Male   | Lewis     | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/bm_lewis.mp3) | bm_lewis |
| Japanese 🇯🇵          | Female | Alpha     | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/jf_alpha.mp3) | jf_alpha |
| Japanese 🇯🇵          | Female | Gongitsune| [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/jf_gongitsune.mp3) | jf_gongitsune |
| Japanese 🇯🇵          | Female | Nezumi    | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/jf_nezumi.mp3) | jf_nezumi |
| Japanese 🇯🇵          | Female | Tebukuro  | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/jf_tebukuro.mp3) | jf_tebukuro |
| Japanese 🇯🇵          | Male   | Kumo      | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/jm_kumo.mp3) | jm_kumo |
| Mandarin Chinese 🇨🇳  | Female | Xiaobei   | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/zf_xiaobei.mp3) | zf_xiaobei |
| Mandarin Chinese 🇨🇳  | Female | Xiaoni    | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/zf_xiaoni.mp3) | zf_xiaoni |
| Mandarin Chinese 🇨🇳  | Female | Xiaoxiao  | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/zf_xiaoxiao.mp3) | zf_xiaoxiao |
| Mandarin Chinese 🇨🇳  | Female | Xiaoyi    | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/zf_xiaoyi.mp3) | zf_xiaoyi |
| Mandarin Chinese 🇨🇳  | Male   | Yunjian   | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/zm_yunjian.mp3) | zm_yunjian |
| Mandarin Chinese 🇨🇳  | Male   | Yunxi     | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/zm_yunxi.mp3) | zm_yunxi |
| Mandarin Chinese 🇨🇳  | Male   | Yunxia    | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/zm_yunxia.mp3) | zm_yunxia |
| Mandarin Chinese 🇨🇳  | Male   | Yunyang   | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/zm_yunyang.mp3) | zm_yunyang |
| Spanish 🇪🇸           | Female | Dora      | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/ef_dora.mp3) | ef_dora |
| Spanish 🇪🇸           | Male   | Alex      | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/em_alex.mp3) | em_alex |
| Spanish 🇪🇸           | Male   | Santa     | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/em_santa.mp3) | em_santa |
| French 🇫🇷            | Female | Siwis     | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/ff_siwis.mp3) | ff_siwis |
| Hindi 🇮🇳             | Female | Alpha     | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/hf_alpha.mp3) | hf_alpha |
| Hindi 🇮🇳             | Female | Beta      | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/hf_beta.mp3) | hf_beta |
| Hindi 🇮🇳             | Male   | Omega     | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/hm_omega.mp3) | hm_omega |
| Hindi 🇮🇳             | Male   | Psi       | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/hm_psi.mp3) | hm_psi |
| Italian 🇮🇹           | Female | Sara      | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/if_sara.mp3) | if_sara |
| Italian 🇮🇹           | Male   | Nicola    | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/im_nicola.mp3) | im_nicola |
| Brazilian Portuguese 🇧🇷 | Female | Dora   | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/pf_dora.mp3) | pf_dora |
| Brazilian Portuguese 🇧🇷 | Male   | Alex   | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/pm_alex.mp3) | pm_alex |
| Brazilian Portuguese 🇧🇷 | Male   | Santa  | [▶ Play](https://beecho01.github.io/Kokoro-TTS/docs/audio/pm_santa.mp3) | pm_santa |

---

## 🛠 Troubleshooting
- First word is cut off
Add a short delay before playback, or adjust server settings.
- No sound
Check server_url and make sure Kokoro FastAPI is running.
- Wrong voice
Verify the voice exists on your Kokoro server.

---

## 🙏 Credits

Kokoro FastAPI backend: [@remsky](https://github.com/remsky)
