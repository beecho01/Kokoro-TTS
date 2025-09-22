# Audio Preview System Documentation

## Overview

The Kokoro TTS integration includes a comprehensive audio preview system that allows users to test different personas with custom text directly from the configuration interface.

## Architecture

### 1. Frontend UI Components

**Preview Text Field:**
- Appears when a persona is selected
- Pre-filled with default text: "Hello, this is a preview of the selected persona."
- Users can customize the preview text
- Supports internationalization

**Preview Button:**
- 🔊 Preview Audio button appears when preview text is available
- Uses Home Assistant's button selector for seamless integration
- Triggers real-time audio generation

### 2. Backend WebSocket API

**WebSocket Command:** `kokoro_tts/preview_audio`

**Required Parameters:**
- `base_url`: Kokoro TTS server URL
- `model`: Selected TTS model
- `persona`: Selected persona/voice  
- `text`: Preview text to synthesize

**Optional Parameters:**
- `speed`: Speech speed (0.25-4.0, default: 1.0)
- `format`: Audio format (wav/mp3/ogg, default: wav)
- `sample_rate`: Sample rate (default: 24000)
- `api_key`: Authentication key if required

**Response:**
- `success`: Boolean indicating success/failure
- `audio_data`: Base64-encoded audio data
- `content_type`: MIME type for audio
- `message`: Status or error message

### 3. Integration Flow

1. **User Interaction:**
   - User selects persona from dropdown
   - Preview text field appears with default text
   - User can modify preview text
   - Preview button becomes available

2. **Audio Generation:**
   - User clicks "🔊 Preview Audio" button
   - Frontend collects all form data
   - WebSocket message sent to backend
   - Backend calls Kokoro TTS API
   - Audio data returned as base64

3. **Audio Playback:**
   - Frontend receives base64 audio data
   - Creates audio blob and plays automatically
   - No page refresh or navigation required

## Features

### Smart UI Logic
- Preview components only show when appropriate
- Integrates with three-tier persona filtering
- Preserves user's form data during preview

### Error Handling
- Network error detection and user feedback
- Kokoro API error propagation
- Graceful fallback for missing data

### Internationalization
- Preview text field label translatable
- Button text supports multiple languages
- Default preview text can be localized

### Performance
- 30-second timeout for audio generation
- Base64 encoding for efficient data transfer
- Automatic cleanup of audio URLs

## File Changes

### `config_flow.py`
- Added preview text field to schema
- Added preview button with conditional display
- Implemented WebSocket command handler
- Added button click handling logic

### `const.py`
- Added `CONF_PREVIEW_TEXT` constant
- Added `DEFAULT_PREVIEW_TEXT` constant

### `translations/en.json`
- Added "preview_text" field label
- Added "preview_button" button text

### `__init__.py`
- Registered WebSocket command during setup
- Imported preview function from config_flow

## Usage

1. Navigate to Kokoro TTS integration configuration
2. Complete connection details (base URL, API key)
3. Select desired persona filtering options
4. Choose a specific persona
5. Modify preview text if desired (optional)
6. Click "🔊 Preview Audio" to hear the persona
7. Complete configuration when satisfied

## Technical Notes

- Uses Home Assistant's standard WebSocket API patterns
- Follows Home Assistant UI/UX conventions
- Compatible with existing three-tier filtering system
- Maintains form state during preview operations
- Requires admin privileges for security

This preview system provides an intuitive way for users to test and select the perfect persona for their TTS needs without leaving the configuration interface.