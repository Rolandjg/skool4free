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

def begin(course_name, course_description, pdf_file, model_name):
    if pdf_file is None:
        return "Please upload a PDF file.", ""
    
    # Save the necessary state
    demo.course_name = course_name
    demo.course_description = course_description
    demo.model_name = model_name
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
    threading.Thread(target=process_slides_in_background).start()
    
    # Return the first slide
    demo.current_slide += 1
    return slide_image, f"Slide 1: {slide_text}"

def process_slides_in_background():
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

async def pre_generate_lecture_audio(idx, slide_text):
    model_name = demo.model_name
    # Generate lecture content using the LLM
    lecture_text = llm.generateLecture(demo.course_name, demo.course_description, slide_text, model_name)
    demo.lecture_texts[idx] = lecture_text  # Store lecture text
    
    # Generate the audio asynchronously and store the file path
    audio_file_path = await audio.generate(lecture_text)
    demo.audio_paths[idx] = audio_file_path  # Store audio file path
    print(f"Pre-generated lecture audio for slide {idx + 1}")

def next_slide():
    if demo.current_slide < len(demo.slide_images):
        slide_image = demo.slide_images[demo.current_slide]
        slide_text = demo.slide_contents[demo.current_slide]
        demo.current_slide += 1
        return slide_image, f"Slide {demo.current_slide}: {slide_text}"
    else:
        return None, "Lecture completed."

def play_lecture_audio(slide_text):
    idx = demo.current_slide - 1  # Get the index of the current slide
    if idx < len(demo.audio_paths) and demo.audio_paths[idx]:
        # Use pre-generated audio
        audio_file_path = demo.audio_paths[idx]
    else:
        # If not pre-generated, generate it now
        model_name = demo.model_name
        lecture_text = llm.generateLecture(demo.course_name, demo.course_description, slide_text, model_name)
        audio_file_path = asyncio.run(audio.generate(lecture_text))
        # Store for future use
        demo.lecture_texts[idx] = lecture_text
        demo.audio_paths[idx] = audio_file_path
    return audio_file_path

def process_question(audio_file):
    # Ensure audio file is provided
    if audio_file is None:
        return "No audio question provided.", None

    # Transcribe the audio question using Whisper
    question_text = transcribe_audio(audio_file)

    # Get the selected model name from the state
    model_name = demo.model_name

    # Generate answer using the LLM
    answer_text = llm.generateAnswer(question_text, model_name)

    # Generate the audio asynchronously and get the audio file path
    audio_file_path = asyncio.run(audio.generate(answer_text))

    # Return the transcription and audio file path
    return question_text, audio_file_path

def transcribe_audio(audio_file):
    # Transcribe the audio file using the loaded Whisper model
    result = whisper_model.transcribe(audio_file)
    return result["text"]

# Gradio UI components and logic
with gr.Blocks() as demo:
    demo.slide_images = []
    demo.slide_contents = []
    demo.lecture_texts = []
    demo.audio_paths = []
    demo.course_name = ""
    demo.course_description = ""
    demo.current_slide = 0
    demo.model_name = "qwen2.5:3b"  # Default model name

    # Top row: Model selection at top right
    with gr.Row():
        with gr.Column(scale=8):
            gr.Markdown("")  # Empty space
        with gr.Column(scale=1):
            model_choice = gr.Dropdown(
                util.getAvailiableModels(),
                value='qwen2.5:3b',  # Set default value
                label="Choose Model"
            )
        next_slide_button = gr.Button("Next Slide")

    # Main image display
    slide_image_display = gr.Image(value=None, label="Slide", interactive=False)

    # Text display for slide content
    slide_text_display = gr.Textbox(label="Slide Text", interactive=False)

    # Lecture audio output component
    lecture_audio_output = gr.Audio(label="Lecture Audio", interactive=False, autoplay=True)

    # Middle row: Audio recording and transcription
    with gr.Row():
        with gr.Column():
            # Audio recording component without 'source' parameter
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

    with gr.Row():
        start_button = gr.Button("Start")
        

    # Action when the Start button is pressed
    start_button.click(
        fn=begin,
        inputs=[course_name, course_description, pdf_file, model_choice],
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
