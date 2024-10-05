import ollama
import asyncio
import OCR
import audio
import re

SYSTEM = """
You are a professor giving a lecture based on a slideshow. Your role is to deliver a lecture on the topic covered by the current slide, ensuring the lecture is relevant and informative.

Guidelines:

    Immediately start lecturing on the content. Do not introduce yourself or acknowledge external elements.
    Maintain an academic tone that is conversational but knowledgeable. Avoid unnecessary enthusiasm or phrases like "certainly!" or "of course."
    Keep your responses concise, around 6 sentences per slide, ensuring depth without overwhelming detail.
    Always conclude each response by asking if there are any questions.
    Do not just explain the content on the slide—teach about it. Expand on the material in a way that adds context, background, or practical application.
    Focus on the main concepts of the slide. If the slide includes peripheral information (like dates, authors, or chapters), focus on the core educational material.
    If the slide contains a question, read it aloud, provide the answer, and thoroughly explain the reasoning behind the correct response.
    Avoid reading verbatim from the slide. Use the slide as a framework, but your lecture should be a value-added extension of it.
    Do not address the user directly or speak about third parties. Your focus is always on teaching the material effectively.
"""

chat_history = [
    {
        'role': 'system',
        'content': SYSTEM
    }
]

def remove_non_alphanumeric_keep_spaces(input_string):
    return re.sub(r'[^a-zA-Z0-9\s.,]', '', input_string)

def generateLecture(course_name, description, slideshow, model_name):
    print(f"talking about {slideshow} using {model_name}")

    chat_history.append(
        {
            'role': 'user',
            'content': f'course name: "{course_name}", course description: "{description}", slide content: "{slideshow}"'
        }
    )

    message = ollama.chat(
        model=model_name,
        messages=chat_history,
        options={'system':SYSTEM}
    )
    final = remove_non_alphanumeric_keep_spaces(message['message']['content'])
    chat_history.append(
        {
            'role':'assistant',
            'content': final
        }
    )
    print(final)
    return final

def generateAnswer(text, model_name):
    print(f"resonding to {text} using {model_name}")

    chat_history.append(
        {
            'role': 'user',
            'content': f'question from user: {text}'
        }
    )
    message = ollama.chat(
            model=model_name,
        messages=chat_history,
        options={'system':SYSTEM}
    )

    final = remove_non_alphanumeric_keep_spaces(message['message']['content'])
    chat_history.append(
        {
            'role':'assistant',
            'content': final
        }
    )
    print(final)
    return final

if __name__ == "__main__":
    generateLecture("discrete structures", "this is an introductory course to discrete structures", "Undirected graphs: cool", "qwen2.5:3b")
    # asyncio.run(audio.generate(generateAnswer("So undirected graphs don't have arrows? How do we know which vertex points to which?")))
