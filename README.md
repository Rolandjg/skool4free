# skool4free
Have local llm teach you based on provided slideshow

This project is an interactive lecture application built using Gradio. It allows users to upload a PDF slideshow, receive a lecture based on the content of each slide, and ask questions via voice input. The app uses a combination of OCR, text-to-speech (TTS), and a large language model (LLM) to provide a dynamic and engaging learning experience.

# Features

    PDF Slideshow Upload: Upload a PDF that serves as the basis for the lecture.
    OCR for Slide Content: Text content is extracted from each slide using Optical Character Recognition (OCR).
    Lecture Generation: A lecture is generated for each slide using an LLM. Users can choose from a list of models.
    Audio Playback: Lecture audio is generated and played automatically in the browser.
    Voice Questions: Users can ask questions via voice, and the LLM provides a spoken response.
    Asynchronous Processing: Slide content and lecture audio are processed in the background, reducing wait times between slides.

# Technologies Used

    Python: Core programming language.
    Gradio: For building the web-based UI.
    Whisper: For transcribing user voice inputs.
    EasyOCR: For extracting text from the slides.
    Ollama LLM: For generating the lecture and answering questions.
    Edge TTS: For generating the lecture and answer audio.
    lmdeploy: For vision language models.

# Installation
    1. Install ollama for your system at ollama.com
    2. Install a language model like llama3.2 or qwen2.5:3B
    3. git clone this repo
    4. pip install -r requirements.txt

    Additional libraries:
        On Ubuntu:
          sudo apt install poppler-utils
        On Macos:
          brew install poppler

# Usage

  Start the application by running the following command:  
    python ui.py
  
  This will launch the Gradio interface locally. You will see a URL in your terminal that looks something like this:
    
    Running on local URL:  http://127.0.0.1:7860/
  
  Upload PDF and Enter Course Information
  
      Upload a PDF file containing the slideshow.
      Enter the course name and a brief course description.
      Select a model from the "Choose Model" dropdown (default: qwen2.5:3b).
      Click Start to begin the lecture.
  
  Navigate Between Slides
  
      The first slide will be displayed along with the generated lecture audio, which plays automatically.
      Click Next Slide to move to the next slide, which will also play the corresponding audio.
  
  Ask Questions
  
      Use the "Ask a question" section to record a voice question.
      Click Submit Question to have your question transcribed, and the LLM will respond with a spoken answer, which will be played automatically.

Tested on Fedora Linux with python 12.5 cuda 11.8
