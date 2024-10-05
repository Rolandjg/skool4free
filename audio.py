import asyncio
import edge_tts
import os

OUTPUT_DIR = "audio"

# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

async def generate_to_file(text, voice_name, output_file):
    """Generate audio from text and save it to a file."""
    communicate = edge_tts.Communicate(text, voice_name)
    await communicate.save(output_file)

def getAvailiableVoices():
    voices = asyncio.run(edge_tts.list_voices())
    result = []

    for voice in voices:
        result.append(voice['ShortName'])

    return result

def generate_sync(text, voice_name) -> bytes:
    return asyncio.run(generate(text, voice_name))

if __name__ == "__main__":
    asyncio.run(generate("Test audio", "en-US-AvaNeural"))
    