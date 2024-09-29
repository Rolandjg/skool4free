import gradio as gr
import whisper
import shutil
import os
import asyncio
import threading
import llm
import OCR
import PDFtoIMG 
import audio
import util

# Ensure necessary directories exist
os.makedirs("pdfs", exist_ok=True)
os.makedirs("slides", exist_ok=True)
os.makedirs("audio", exist_ok=True)

whisper_model = whisper.load_model("base")

def begin(course_name, course_description, pdf_file, model_name, voice_name):
    try:
        if pdf_file is None:
            return "Please upload a PDF file.", ""
        
        # Save the necessary state
        demo.course_name = course_name
        demo.course_description = course_description
        demo.model_name = model_name
        demo.voice = voice_name  # Store the selected voice
        demo.current_slide = 0
        
        util.clearFolder(os.path.abspath('slides/'))
        
        # Convert PDF to images
        output_dir = "slides"
        PDFtoIMG.pdf_to_images(pdf_file.name, output_dir)
        
        # Get list of slide images
        slide_images = sorted(
            [os.path.join(output_dir, img) for img in os.listdir(output_dir) if img.endswith('.png')]
        )
        
        if not slide_images:
            return "No slides were generated from the PDF.", ""
        
        demo.slide_images = slide_images
        num_slides = len(slide_images)
        demo.slide_contents = [None] * num_slides
        demo.lecture_texts = [None] * num_slides
        demo.audio_paths = [None] * num_slides
        
        # Process the first slide immediately
        slide_image = slide_images[0]
        slide_text = OCR.ocr(slide_image, 'en')
        demo.slide_contents[0] = slide_text  # Store the processed content
        
        # Pre-generate lecture content and audio for the first slide
        asyncio.run(pre_generate_lecture_audio(0, slide_text))
        
        # Start background processing for remaining slides
        threading.Thread(target=process_slides_in_background, daemon=True).start()
        
        # Return the first slide
        demo.current_slide += 1
        return slide_image, f"Slide 1: {slide_text}"
    except Exception as e:
        print(f"Error in begin: {e}")
        return "An error occurred while starting the lecture.", ""

def process_slides_in_background():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        tasks = []
        for idx in range(1, len(demo.slide_images)):
            slide_image = demo.slide_images[idx]
            # Perform OCR
            slide_text = OCR.ocr(slide_image, 'en')
            demo.slide_contents[idx] = slide_text  # Store the processed content
            
            # Pre-generate lecture content and audio
            task = loop.create_task(pre_generate_lecture_audio(idx, slide_text))
            tasks.append(task)
        loop.run_until_complete(asyncio.gather(*tasks))
        loop.close()
    except Exception as e:
        print(f"Error in background processing: {e}")

async def pre_generate_lecture_audio(idx, slide_text):
    try:
        model_name = demo.model_name
        voice_name = demo.voice

        # Generate lecture content using the LLM
        lecture_text = llm.generateLecture(demo.course_name, demo.course_description, slide_text, model_name)
        demo.lecture_texts[idx] = lecture_text  # Store lecture text

        # Generate the audio asynchronously and store the binary data
        audio_file_data = await audio.generate(lecture_text, voice_name)
        demo.audio_paths[idx] = audio_file_data  # Store audio data
        print(f"Pre-generated lecture audio for slide {idx + 1}")
    except Exception as e:
        print(f"Error in pre_generate_lecture_audio for slide {idx + 1}: {e}")

def next_slide():
    try:
        if demo.current_slide < len(demo.slide_images):
            slide_image = demo.slide_images[demo.current_slide]
            slide_text = demo.slide_contents[demo.current_slide]
            demo.current_slide += 1
            return slide_image, f"Slide {demo.current_slide}: {slide_text}"
        else:
            return None, "Lecture completed."
    except Exception as e:
        print(f"Error in next_slide: {e}")
        return None, "An error occurred while moving to the next slide."

def play_lecture_audio(slide_text):
    try:
        voice_name = demo.voice
        idx = demo.current_slide - 1  # Get the index of the current slide

        if idx < len(demo.audio_paths) and demo.audio_paths[idx]:
            # Use pre-generated audio
            audio_file_data = demo.audio_paths[idx]
        else:
            # If not pre-generated, generate it now
            model_name = demo.model_name
            lecture_text = llm.generateLecture(demo.course_name, demo.course_description, slide_text, model_name)
            # Corrected asyncio.run call
            audio_file_data = asyncio.run(audio.generate(lecture_text, voice_name))
            # Store for future use
            demo.lecture_texts[idx] = lecture_text
            demo.audio_paths[idx] = audio_file_data
        return audio_file_data
    except Exception as e:
        print(f"Error in play_lecture_audio: {e}")
        return None

def process_question(audio_file):
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

        # Generate the audio asynchronously and get the audio data
        audio_file_data = asyncio.run(audio.generate(answer_text, voice_name))

        # Return the transcription and audio data
        return question_text, audio_file_data
    except Exception as e:
        print(f"Error in process_question: {e}")
        return "An error occurred while processing your question.", None

def transcribe_audio(audio_file):
    try:
        # Transcribe the audio file using the loaded Whisper model
        result = whisper_model.transcribe(audio_file)
        transcription = result["text"]
        print(f"Transcription result: {transcription}")
        return transcription
    except Exception as e:
        print(f"Error in transcribe_audio: {e}")
        return "An error occurred during transcription."

# Gradio UI components and logic
with gr.Blocks() as demo:
    # Initialize state variables
    demo.slide_images = []
    demo.slide_contents = []
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
            gr.Markdown("# Interactive Lecture Application")
        with gr.Column(scale=2):
            model_choice = gr.Dropdown(
                util.getAvailiableModels(),
                value='qwen2.5:3b',  # Set default value
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
                sources='microphone',  # Correct parameter name
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

    # Start button
    with gr.Row():
        start_button = gr.Button("Start")

    # Action when the Start button is pressed
    start_button.click(
        fn=begin,
        inputs=[course_name, course_description, pdf_file, model_choice, voice_choice],
        outputs=[slide_image_display, slide_text_display]
    ).then(
        fn=play_lecture_audio,
        inputs=[slide_text_display],
        outputs=[lecture_audio_output]
    )

    # Action when the Next Slide button is pressed
    next_slide_button.click(
        fn=next_slide,
        inputs=[],
        outputs=[slide_image_display, slide_text_display]
    ).then(
        fn=play_lecture_audio,
        inputs=[slide_text_display],
        outputs=[lecture_audio_output]
    )

    # Action when the Question button is pressed
    question_button.click(
        fn=process_question,
        inputs=[question_audio],
        outputs=[transcription, answer_audio_output]
    )

demo.launch(share=True)
