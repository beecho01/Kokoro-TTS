/*
Audio Preview Frontend Implementation Example
===========================================

This file shows how the frontend can interact with the Kokoro TTS audio preview WebSocket API.
This would typically be integrated into Home Assistant's frontend configuration flow rendering.

In Home Assistant, the button click would trigger this JavaScript code to:
1. Collect form data (base_url, model, persona, preview_text, etc.)
2. Send WebSocket command to backend
3. Receive base64 audio data
4. Play the audio in the browser

The Home Assistant frontend would handle this automatically when the button selector is used
with the WebSocket command we registered.
*/

// Example frontend JavaScript for audio preview
async function previewAudio(formData) {
    // Extract configuration from the current form
    const message = {
        type: "kokoro_tts/preview_audio",
        base_url: formData.base_url,
        model: formData.model, 
        persona: formData.persona,
        text: formData.preview_text || "Hello, this is a preview of the selected persona.",
        speed: parseFloat(formData.speed || "1.0"),
        format: formData.format || "wav",
        sample_rate: formData.sample_rate || "24000",
        api_key: formData.api_key
    };
    
    // Send WebSocket command to Home Assistant
    try {
        const response = await window.hassConnection.sendMessagePromise(message);
        
        if (response.success) {
            // Convert base64 to audio blob and play
            const audioData = atob(response.audio_data);
            const audioBytes = new Uint8Array(audioData.length);
            for (let i = 0; i < audioData.length; i++) {
                audioBytes[i] = audioData.charCodeAt(i);
            }
            
            const audioBlob = new Blob([audioBytes], { type: response.content_type });
            const audioUrl = URL.createObjectURL(audioBlob);
            
            // Create and play audio element
            const audio = new Audio(audioUrl);
            audio.play();
            
            // Clean up URL after playing
            audio.addEventListener('ended', () => {
                URL.revokeObjectURL(audioUrl);
            });
            
            console.log("Audio preview played successfully");
        } else {
            console.error("Preview failed:", response.message);
            alert("Preview failed: " + response.message);
        }
    } catch (error) {
        console.error("WebSocket error:", error);
        alert("Network error during preview: " + error.message);
    }
}

/*
Home Assistant Config Flow Integration:
=====================================

The button selector we added in config_flow.py:

    schema[vol.Optional("preview_button")] = selector.selector({
        "button": {
            "label": "🔊 Preview Audio",
        }
    })

When clicked, Home Assistant's frontend will:
1. Collect all form field values
2. Look for a registered WebSocket command: "kokoro_tts/preview_audio"  
3. Call our websocket_preview_audio function with the form data
4. Handle the response and play the audio automatically

The WebSocket command we registered:

    @require_admin
    @websocket_command({
        vol.Required("type"): "kokoro_tts/preview_audio",
        vol.Required("base_url"): str,
        vol.Required("model"): str,
        vol.Required("persona"): str,
        vol.Required("text"): str,
        // ... other optional parameters
    })
    async def websocket_preview_audio(hass, connection, msg):
        # Generate TTS audio and return base64 data
        // Home Assistant frontend will automatically play the audio

This creates a seamless audio preview experience where:
- User types preview text
- User clicks "🔊 Preview Audio" button  
- Audio plays immediately in the browser
- No page refresh or navigation required
*/