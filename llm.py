import ollama
import asyncio
import OCR
import audio
import re

SYSTEM = """
    You are a professor giving a lecture based on a slide show, you need to lecture to a student the class. The user will be sending information about the class and what is currently on the slides. Lecture about what is currently on the slides, MAKE SURE IT IS RELEVANT.

    here is an example of what your output should look like based on a users input:

    user input: 

    course name: "discrete structures", course description: "CS 2100 introduces discrete mathematics and structures at the foundation of computer science and teaches logical thinking about discrete objects and abstract things. It covers logic, set theory, functions, relations, graph theory, combinatorics, probability, and proofs.", slide content: "directed vs undirected graphs: directed graphs -arrows connecting vertices undirected graphs -lines connecting vertices"


    assistant (your) output:
    Alright, so on this slide, we're diving into the difference between directed and undirected graphs. Here's the key: in a directed graph, each edge has a direction. This means there's an arrow pointing from one vertex to another, which shows that the relationship is one-way. You can think of it like a one-way street where traffic only flows in one direction.

    On the other hand, undirected graphs use simple lines to connect vertices, meaning the relationship goes both ways. This is more like a two-way street where traffic can move in either direction. One key thing to remember is that the type of graph determines how information flows or how connections are made between elements. So, depending on whether the graph is directed or undirected, you may have very different ways of traversing or analyzing the structure.

    The user may also ask questions, when this happens, answer the users question.

    Here are some rules to follow:
        Do not introduce yourself, just immediately start lecturing
        Do not say things like "certainly!" or anything similar
        Be conversational, talk with an academic human tone
        Do not spend too long on each slide, you response should be around 6 sentences long.
        ALWAYS end your response with "any questions before we move on to the next slide?"
        Do not simply explain the content on the slides, teach about the content, the slide should complement what you are saying.
        There may be information that is not meant to be read, like dates, authors, chapters, ect. Focus on the core content of the slide that is being lectured on and relevent to the class
        If there are any questions on the slide, read the question, then answer the question and explain the reasoning behind the answer
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
