import asyncio
import edge_tts
import os

OUTPUT_DIR = "audio"

# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

async def generate(text, voice) -> bytes:
    """Generate audio from text and return the binary data."""
    # Generate a unique filename for each audio file
    output_file = os.path.join(OUTPUT_DIR, f"audio_{hash(text)}.mp3")
    
    communicate = edge_tts.Communicate(text, voice, rate="+25%")
    with open(output_file, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
    
    # Read the binary data
    with open(output_file, "rb") as f:
        audio_data = f.read()
    
    # Optionally, delete the audio file to save space
    # os.remove(output_file)
    
    # Return the audio binary data
    return audio_data

def getAvailiableVoices():
    voices = asyncio.run(edge_tts.list_voices())
    result = []

    for voice in voices:
        result.append(voice['ShortName'])

    return result

if __name__ == "__main__":
    asyncio.run(generate("Test audio", "en-US-AvaNeural"))
    