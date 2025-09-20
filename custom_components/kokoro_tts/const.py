# custom_components/kokoro_tts/const.py
DOMAIN = "kokoro_tts"

CONF_BASE_URL = "base_url"
CONF_API_KEY = "api_key"
CONF_MODEL = "model"
CONF_VOICE = "voice"
CONF_SPEED = "speed"
CONF_FORMAT = "format"
CONF_SAMPLE_RATE = "sample_rate"
CONF_PAD_MS = "pad_ms"

# Default values
DEFAULT_API_KEY = "not-needed"
DEFAULT_MODEL = "kokoro"
DEFAULT_VOICE = "bm_lewis"
DEFAULT_SPEED = 0.9
DEFAULT_FORMAT = "wav"
DEFAULT_SAMPLE_RATE = 24000
DEFAULT_PAD_MS = 200

# Consolidated defaults dictionary
DEFAULTS = {
    CONF_API_KEY: DEFAULT_API_KEY,
    CONF_MODEL: DEFAULT_MODEL,
    CONF_VOICE: DEFAULT_VOICE,
    CONF_SPEED: DEFAULT_SPEED,
    CONF_FORMAT: DEFAULT_FORMAT,
    CONF_SAMPLE_RATE: DEFAULT_SAMPLE_RATE,
    CONF_PAD_MS: DEFAULT_PAD_MS,
}