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
  🎧 <strong>Listen to a preview:</strong><br><br>
  <audio controls src="docs/audio/af_heart.mp3"></audio>
</p>

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

| Language             | Gender | Name      | Preview | Persona Code |
|----------------------|--------|-----------|---------|--------------|
| American English 🇺🇸 | Female | Heart     | <audio controls src="docs/audio/af_heart.mp3"></audio> | af_heart |
| American English 🇺🇸 | Female | Alloy     | <audio controls src="docs/audio/af_alloy.mp3"></audio> | af_alloy |
| American English 🇺🇸 | Female | Aoede     | <audio controls src="docs/audio/af_aoede.mp3"></audio> | af_aoede |
| American English 🇺🇸 | Female | Bella     | <audio controls src="docs/audio/af_bella.mp3"></audio> | af_bella |
| American English 🇺🇸 | Female | Jessica   | <audio controls src="docs/audio/af_jessica.mp3"></audio> | af_jessica |
| American English 🇺🇸 | Female | Kore      | <audio controls src="docs/audio/af_kore.mp3"></audio> | af_kore |
| American English 🇺🇸 | Female | Nicole    | <audio controls src="docs/audio/af_nicole.mp3"></audio> | af_nicole |
| American English 🇺🇸 | Female | Nova      | <audio controls src="docs/audio/af_nova.mp3"></audio> | af_nova |
| American English 🇺🇸 | Female | River     | <audio controls src="docs/audio/af_river.mp3"></audio> | af_river |
| American English 🇺🇸 | Female | Sarah     | <audio controls src="docs/audio/af_sarah.mp3"></audio> | af_sarah |
| American English 🇺🇸 | Female | Sky       | <audio controls src="docs/audio/af_sky.mp3"></audio> | af_sky |
| American English 🇺🇸 | Male   | Adam      | <audio controls src="docs/audio/am_adam.mp3"></audio> | am_adam |
| American English 🇺🇸 | Male   | Echo      | <audio controls src="docs/audio/am_echo.mp3"></audio> | am_echo |
| American English 🇺🇸 | Male   | Eric      | <audio controls src="docs/audio/am_eric.mp3"></audio> | am_eric |
| American English 🇺🇸 | Male   | Fenrir    | <audio controls src="docs/audio/am_fenrir.mp3"></audio> | am_fenrir |
| American English 🇺🇸 | Male   | Liam      | <audio controls src="docs/audio/am_liam.mp3"></audio> | am_liam |
| American English 🇺🇸 | Male   | Michael   | <audio controls src="docs/audio/am_michael.mp3"></audio> | am_michael |
| American English 🇺🇸 | Male   | Onyx      | <audio controls src="docs/audio/am_onyx.mp3"></audio> | am_onyx |
| American English 🇺🇸 | Male   | Puck      | <audio controls src="docs/audio/am_puck.mp3"></audio> | am_puck |
| American English 🇺🇸 | Male   | Santa     | <audio controls src="docs/audio/am_santa.mp3"></audio> | am_santa |
| British English 🇬🇧  | Female | Alice     | <audio controls src="docs/audio/bf_alice.mp3"></audio> | bf_alice |
| British English 🇬🇧  | Female | Emma      | <audio controls src="docs/audio/bf_emma.mp3"></audio> | bf_emma |
| British English 🇬🇧  | Female | Isabella  | <audio controls src="docs/audio/bf_isabella.mp3"></audio> | bf_isabella |
| British English 🇬🇧  | Female | Lily      | <audio controls src="docs/audio/bf_lily.mp3"></audio> | bf_lily |
| British English 🇬🇧  | Male   | Daniel    | <audio controls src="docs/audio/bm_daniel.mp3"></audio> | bm_daniel |
| British English 🇬🇧  | Male   | Fable     | <audio controls src="docs/audio/bm_fable.mp3"></audio> | bm_fable |
| British English 🇬🇧  | Male   | George    | <audio controls src="docs/audio/bm_george.mp3"></audio> | bm_george |
| British English 🇬🇧  | Male   | Lewis     | <audio controls src="docs/audio/bm_lewis.mp3"></audio> | bm_lewis |
| Japanese 🇯🇵          | Female | Alpha     | <audio controls src="docs/audio/jf_alpha.mp3"></audio> | jf_alpha |
| Japanese 🇯🇵          | Female | Gongitsune| <audio controls src="docs/audio/jf_gongitsune.mp3"></audio> | jf_gongitsune |
| Japanese 🇯🇵          | Female | Nezumi    | <audio controls src="docs/audio/jf_nezumi.mp3"></audio> | jf_nezumi |
| Japanese 🇯🇵          | Female | Tebukuro  | <audio controls src="docs/audio/jf_tebukuro.mp3"></audio> | jf_tebukuro |
| Japanese 🇯🇵          | Male   | Kumo      | <audio controls src="docs/audio/jm_kumo.mp3"></audio> | jm_kumo |
| Mandarin Chinese 🇨🇳  | Female | Xiaobei   | <audio controls src="docs/audio/zf_xiaobei.mp3"></audio> | zf_xiaobei |
| Mandarin Chinese 🇨🇳  | Female | Xiaoni    | <audio controls src="docs/audio/zf_xiaoni.mp3"></audio> | zf_xiaoni |
| Mandarin Chinese 🇨🇳  | Female | Xiaoxiao  | <audio controls src="docs/audio/zf_xiaoxiao.mp3"></audio> | zf_xiaoxiao |
| Mandarin Chinese 🇨🇳  | Female | Xiaoyi    | <audio controls src="docs/audio/zf_xiaoyi.mp3"></audio> | zf_xiaoyi |
| Mandarin Chinese 🇨🇳  | Male   | Yunjian   | <audio controls src="docs/audio/zm_yunjian.mp3"></audio> | zm_yunjian |
| Mandarin Chinese 🇨🇳  | Male   | Yunxi     | <audio controls src="docs/audio/zm_yunxi.mp3"></audio> | zm_yunxi |
| Mandarin Chinese 🇨🇳  | Male   | Yunxia    | <audio controls src="docs/audio/zm_yunxia.mp3"></audio> | zm_yunxia |
| Mandarin Chinese 🇨🇳  | Male   | Yunyang   | <audio controls src="docs/audio/zm_yunyang.mp3"></audio> | zm_yunyang |
| Spanish 🇪🇸           | Female | Dora      | <audio controls src="docs/audio/ef_dora.mp3"></audio> | ef_dora |
| Spanish 🇪🇸           | Male   | Alex      | <audio controls src="docs/audio/em_alex.mp3"></audio> | em_alex |
| Spanish 🇪🇸           | Male   | Santa     | <audio controls src="docs/audio/em_santa.mp3"></audio> | em_santa |
| French 🇫🇷            | Female | Siwis     | <audio controls src="docs/audio/ff_siwis.mp3"></audio> | ff_siwis |
| Hindi 🇮🇳             | Female | Alpha     | <audio controls src="docs/audio/hf_alpha.mp3"></audio> | hf_alpha |
| Hindi 🇮🇳             | Female | Beta      | <audio controls src="docs/audio/hf_beta.mp3"></audio> | hf_beta |
| Hindi 🇮🇳             | Male   | Omega     | <audio controls src="docs/audio/hm_omega.mp3"></audio> | hm_omega |
| Hindi 🇮🇳             | Male   | Psi       | <audio controls src="docs/audio/hm_psi.mp3"></audio> | hm_psi |
| Italian 🇮🇹           | Female | Sara      | <audio controls src="docs/audio/if_sara.mp3"></audio> | if_sara |
| Italian 🇮🇹           | Male   | Nicola    | <audio controls src="docs/audio/im_nicola.mp3"></audio> | im_nicola |
| Brazilian Portuguese 🇧🇷 | Female | Dora   | <audio controls src="docs/audio/pf_dora.mp3"></audio> | pf_dora |
| Brazilian Portuguese 🇧🇷 | Male   | Alex   | <audio controls src="docs/audio/pm_alex.mp3"></audio> | pm_alex |
| Brazilian Portuguese 🇧🇷 | Male   | Santa  | <audio controls src="docs/audio/pm_santa.mp3"></audio> | pm_santa |

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
