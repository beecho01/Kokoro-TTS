# custom_components/kokoro_tts/const.py
DOMAIN = "kokoro_tts"

CONF_BASE_URL = "base_url"
CONF_API_KEY = "api_key"
CONF_MODEL = "model"
CONF_PERSONA = "persona"
CONF_LANGUAGE = "language"
CONF_SEX = "sex"
CONF_SPEED = "speed"
CONF_FORMAT = "format"
CONF_SAMPLE_RATE = "sample_rate"
CONF_PREVIEW_TEXT = "preview_text"

# Default values
DEFAULT_API_KEY = "not-needed"
DEFAULT_MODEL = "kokoro"
DEFAULT_PERSONA = None
DEFAULT_LANGUAGE = "All Languages"
DEFAULT_SEX = "All"
DEFAULT_SPEED = 0.9
DEFAULT_FORMAT = "wav"
DEFAULT_SAMPLE_RATE = 24000
DEFAULT_PREVIEW_TEXT = "Hello, this is a preview of the selected persona."

# Voice mapping: technical_name -> (language, gender, display_name)
PERSONA_MAPPINGS = {
    # American English (🇺🇸)
    "af_heart": ("American English", "Female", "Heart"),
    "af_alloy": ("American English", "Female", "Alloy"),
    "af_aoede": ("American English", "Female", "Aoede"),
    "af_bella": ("American English", "Female", "Bella"),
    "af_jessica": ("American English", "Female", "Jessica"),
    "af_kore": ("American English", "Female", "Kore"),
    "af_nicole": ("American English", "Female", "Nicole"),
    "af_nova": ("American English", "Female", "Nova"),
    "af_river": ("American English", "Female", "River"),
    "af_sarah": ("American English", "Female", "Sarah"),
    "af_sky": ("American English", "Female", "Sky"),
    "am_adam": ("American English", "Male", "Adam"),
    "am_echo": ("American English", "Male", "Echo"),
    "am_eric": ("American English", "Male", "Eric"),
    "am_fenrir": ("American English", "Male", "Fenrir"),
    "am_liam": ("American English", "Male", "Liam"),
    "am_michael": ("American English", "Male", "Michael"),
    "am_onyx": ("American English", "Male", "Onyx"),
    "am_puck": ("American English", "Male", "Puck"),
    "am_santa": ("American English", "Male", "Santa"),
    
    # British English (🇬🇧)
    "bf_alice": ("British English", "Female", "Alice"),
    "bf_emma": ("British English", "Female", "Emma"),
    "bf_isabella": ("British English", "Female", "Isabella"),
    "bf_lily": ("British English", "Female", "Lily"),
    "bm_daniel": ("British English", "Male", "Daniel"),
    "bm_fable": ("British English", "Male", "Fable"),
    "bm_george": ("British English", "Male", "George"),
    "bm_lewis": ("British English", "Male", "Lewis"),
    
    # Japanese (🇯🇵)
    "jf_alpha": ("Japanese", "Female", "Alpha"),
    "jf_gongitsune": ("Japanese", "Female", "Gongitsune"),
    "jf_nezumi": ("Japanese", "Female", "Nezumi"),
    "jf_tebukuro": ("Japanese", "Female", "Tebukuro"),
    "jm_kumo": ("Japanese", "Male", "Kumo"),
    
    # Mandarin Chinese (🇨🇳)
    "zf_xiaobei": ("Mandarin Chinese", "Female", "Xiaobei"),
    "zf_xiaoni": ("Mandarin Chinese", "Female", "Xiaoni"),
    "zf_xiaoxiao": ("Mandarin Chinese", "Female", "Xiaoxiao"),
    "zf_xiaoyi": ("Mandarin Chinese", "Female", "Xiaoyi"),
    "zm_yunjian": ("Mandarin Chinese", "Male", "Yunjian"),
    "zm_yunxi": ("Mandarin Chinese", "Male", "Yunxi"),
    "zm_yunxia": ("Mandarin Chinese", "Male", "Yunxia"),
    "zm_yunyang": ("Mandarin Chinese", "Male", "Yunyang"),
    
    # Spanish (🇪🇸)
    "ef_dora": ("Spanish", "Female", "Dora"),
    "em_alex": ("Spanish", "Male", "Alex"),
    "em_santa": ("Spanish", "Male", "Santa"),
    
    # French (🇫🇷)
    "ff_siwis": ("French", "Female", "Siwis"),
    
    # Hindi (🇮🇳)
    "hf_alpha": ("Hindi", "Female", "Alpha"),
    "hf_beta": ("Hindi", "Female", "Beta"),
    "hm_omega": ("Hindi", "Male", "Omega"),
    "hm_psi": ("Hindi", "Male", "Psi"),
    
    # Italian (🇮🇹)
    "if_sara": ("Italian", "Female", "Sara"),
    "im_nicola": ("Italian", "Male", "Nicola"),
    
    # Brazilian Portuguese (🇧🇷)
    "pf_dora": ("Brazilian Portuguese", "Female", "Dora"),
    "pm_alex": ("Brazilian Portuguese", "Male", "Alex"),
    "pm_santa": ("Brazilian Portuguese", "Male", "Santa"),
}

# Language groups for filtering
LANGUAGE_OPTIONS = [
    "American English",
    "British English", 
    "Japanese",
    "Mandarin Chinese",
    "Spanish",
    "French",
    "Hindi",
    "Italian",
    "Brazilian Portuguese",
    "All Languages"
]

# Sex options for filtering
SEX_OPTIONS = [
    "Female",
    "Male", 
    "All"
]

# Consolidated defaults dictionary
DEFAULTS = {
    CONF_API_KEY: DEFAULT_API_KEY,
    CONF_MODEL: DEFAULT_MODEL,
    CONF_PERSONA: DEFAULT_PERSONA,  # None - user must select
    CONF_LANGUAGE: DEFAULT_LANGUAGE,
    CONF_SEX: DEFAULT_SEX,
    CONF_SPEED: DEFAULT_SPEED,
    CONF_FORMAT: DEFAULT_FORMAT,
    CONF_SAMPLE_RATE: DEFAULT_SAMPLE_RATE,
}