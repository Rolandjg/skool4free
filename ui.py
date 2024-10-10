import gradio as gr
import whisper
import shutil
import os
import asyncio
import llm
import OCR
import PDFtoIMG
import audio
import util
import re

# Ensure necessary directories exist
os.makedirs("pdfs", exist_ok=True)
os.makedirs("slides", exist_ok=True)
os.makedirs("audio", exist_ok=True)

whisper_model = whisper.load_model("tiny.en")

def begin(course_name, course_description, pdf_file, model_name, voice_name, start_number):
    if pdf_file is None:
        return "Please upload a PDF file.", ""

    # Use the file path directly
    pdf_path = pdf_file.name
    print(f"PDF Path: {pdf_path}")

    util.clearFolder(os.path.abspath("slides/"))

    # Convert PDF to images
    output_dir = "slides"
    PDFtoIMG.pdf_to_images(pdf_path, output_dir)

    # Get list of slide images
    slide_images = [img for img in os.listdir(output_dir) if img.endswith('.png')]
    slide_images.sort(key=natural_sort_key)
    slide_images = [os.path.join(output_dir, img) for img in slide_images]
    slide_images = slide_images[int(start_number):]

    if not slide_images:
        return "No slides were generated from the PDF.", ""

    # Initialize an empty list to store slide contents
    slide_contents = []

    # Extract text from each slide using OCR
    for slide_image in slide_images:
        if OCR.is_vision_available():
            slide_text = OCR.ocr_vision(slide_image)
        else:
            slide_text = OCR.ocr(slide_image, 'en')
        slide_contents.append((slide_image, slide_text))
    OCR.unload_vision_model() # Unload vision model to save precious VRAM

    # Store slide contents and model_name in state
    demo.slides = slide_contents
    demo.course_name = course_name
    demo.course_description = course_description
    demo.current_slide = 0
    demo.model_name = model_name
    demo.voice = voice_name

    # Initialize lecture_texts and audio_paths lists
    num_slides = len(demo.slides)
    demo.lecture_texts = [None] * num_slides
    demo.audio_paths = [None] * num_slides

    # Return the first slide image and text to update the UI
    slide_image, slide_text = demo.slides[demo.current_slide]
    demo.current_slide += 1  # Increment slide index

    return slide_image, f"Slide 1: {slide_text}"

def next_slide():
    print("next slide")
    try:
        if demo.current_slide < len(demo.slides):
            slide_image, slide_text = demo.slides[demo.current_slide]
            demo.current_slide += 1
            return slide_image, f"Slide {demo.current_slide}: {slide_text}"
        else:
            return None, "Lecture completed."
    except Exception as e:
        print(f"Error in next_slide: {e}")
        return None, "An error occurred while moving to the next slide."

def play_lecture_audio(speech_text):
    print("playing lecture audio")
    try:
        voice_name = demo.voice
        idx = demo.current_slide - 1  # Get the index of the current slide

        if idx < len(demo.audio_paths) and demo.audio_paths[idx]:
            # Use pre-generated audio
            audio_file_path = demo.audio_paths[idx]
            lecture_text = demo.lecture_texts[idx]
        else:
            # Generate lecture content using the LLM
            model_name = demo.model_name
            lecture_text = llm.generateLecture(
                demo.course_name, demo.course_description, f"slide number {idx}, {speech_text}", model_name
            )

            # Generate the audio synchronously and save to file
            audio_file_path = f"audio/lecture_{idx}.mp3"
            asyncio.run(audio.generate_to_file(lecture_text, voice_name, audio_file_path))

            # Store for future use
            demo.lecture_texts[idx] = lecture_text
            demo.audio_paths[idx] = audio_file_path

        # Return only the audio file path
        return audio_file_path
    except Exception as e:
        print(f"Error in play_lecture_audio: {e}")
        return None


def process_question(audio_file):
    print("processing question")
    try:
        voice_name = demo.voice

        # Ensure audio file is provided
        if audio_file is None:
            return "No audio question provided.", None

        # Transcribe the audio question using Whisper
        question_text = transcribe_audio(audio_file)
        print(f"Transcribed question: {question_text}")

        # Get the selected model name from the state
        model_name = demo.model_name

        # Generate answer using the LLM
        answer_text = llm.generateAnswer(question_text, model_name)
        print(f"Generated answer: {answer_text}")

        # Generate the audio synchronously and save to file
        audio_file_path = f"audio/answer_{demo.current_slide - 1}.mp3"
        asyncio.run(audio.generate_to_file(answer_text, voice_name, audio_file_path))

        # Return the transcription and audio file path
        return question_text, audio_file_path
    except Exception as e:
        print(f"Error in process_question: {e}")
        return "An error occurred while processing your question.", None


def transcribe_audio(audio_file):
    print("transcribing audio")
    try:
        # Transcribe the audio file using the loaded Whisper model
        result = whisper_model.transcribe(audio_file)
        transcription = result["text"]
        print(f"Transcription result: {transcription}")
        return transcription
    except Exception as e:
        print(f"Error in transcribe_audio: {e}")
        return "An error occurred during transcription."

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

# Gradio UI components and logic
with gr.Blocks() as demo:
    # Initialize state variables
    demo.slides = []
    demo.lecture_texts = []
    demo.audio_paths = []
    demo.course_name = ""
    demo.course_description = ""
    demo.current_slide = 0
    demo.model_name = "qwen2.5:3b"  # Default model name
    demo.voice = "en-US-AndrewNeural"  # Default voice

    # Top row: Model and Voice selection at top right
    with gr.Row():
        with gr.Column(scale=6):
            gr.Markdown("# Skool4Free")
        with gr.Column(scale=2):
            model_choice = gr.Dropdown(
                util.getAvailiableModels(),
                value='qwen2.5:3b',
                label="Choose Model"
            )
        with gr.Column(scale=2):
            voice_choice = gr.Dropdown(
                audio.getAvailiableVoices(),
                value="en-US-AndrewNeural",
                label="Choose Voice"
            )
        with gr.Column(scale=2):
            next_slide_button = gr.Button("Next Slide")

    # Main image display
    with gr.Row():
        with gr.Column():
            slide_image_display = gr.Image(value=None, label="Slide", interactive=False)
        with gr.Column():
            slide_text_display = gr.Textbox(label="Slide Text", interactive=False)

    # Lecture audio output component
    with gr.Row():
        with gr.Column():
            lecture_audio_output = gr.Audio(label="Lecture Audio", interactive=False, autoplay=True)

    # Middle row: Audio recording and transcription
    with gr.Row():
        with gr.Column():
            # Audio recording component
            question_audio = gr.Audio(
                sources='microphone',
                label="Ask a question",
                type='filepath',
                interactive=True
            )
            # Button to submit the question
            question_button = gr.Button("Submit Question")
        with gr.Column():
            # Text box for transcription
            transcription = gr.Textbox(label="Your Question")
            # Answer audio output component
            answer_audio_output = gr.Audio(label="Answer Audio", interactive=False, autoplay=True)

    # Bottom row: Course info and file upload
    with gr.Row():
        with gr.Column():
            course_name = gr.Textbox(label="Course Name", placeholder="Enter course name")
        with gr.Column():
            course_description = gr.Textbox(label="Course Description", placeholder="Enter course description")
        with gr.Column():
            pdf_file = gr.File(
                label="Upload PDF",
                file_types=[".pdf"]
            )
        #Start number
        start_number = gr.Number(label="start number")

    # Start button
    with gr.Row():
        start_button = gr.Button("Start")

    # Action when the Start button is pressed
    start_button.click(
        fn=begin,
        inputs=[course_name, course_description, pdf_file, model_choice, voice_choice, start_number],
        outputs=[slide_image_display, slide_text_display]
    ).then(
        fn=play_lecture_audio,
        inputs=[slide_text_display],
        outputs=[lecture_audio_output]  # Only expecting the audio output
    )

    # Action when the Next Slide button is pressed
    next_slide_button.click(
        fn=next_slide,
        inputs=[],
        outputs=[slide_image_display, slide_text_display]
    ).then(
        fn=play_lecture_audio,
        inputs=[slide_text_display],
        outputs=[lecture_audio_output]  # Only expecting the audio output
    )

    # Action when the Question button is pressed
    question_button.click(
        fn=process_question,
        inputs=[question_audio],
        outputs=[transcription, answer_audio_output]
    )

demo.launch(share=False, debug=True)
