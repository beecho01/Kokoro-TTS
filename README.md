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

1. Go to **HACS → Integrations → Custom repositories**.  
2. Add this repository: `https://github.com/beecho01/Kokoro-TTS` with category **Integration**.
3. Search for **Kokoro-TTS** in HACS and install.  
4. Restart Home Assistant.

### Manual

1. Download the latest release from [Releases](../../releases).  
2. Copy the folder `custom_components/kokoro_tts` into your Home Assistant `custom_components` directory.  
3. Restart Home Assistant.

---

## ⚙️ Configuration

Work-in-progress

---

## ▶️ Usage

Work-in-progress

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
