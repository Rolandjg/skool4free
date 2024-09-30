import easyocr
from lmdeploy import pipeline, TurbomindEngineConfig
from lmdeploy.vl import load_image
import os
from PIL import Image

vision = True
try:
    model = 'OpenGVLab/InternVL2-1B'
    pipe = pipeline(model, backend_config=TurbomindEngineConfig(session_len=8192))
except:
    vision = False
    print("could not load vision model")

def is_vision_available():
    return vision 

def ocr(image_path, language):
    print(f"processing {image_path}")

    reader = easyocr.Reader(['en'])
    result = reader.readtext(image_path)
    final = ""
    for words in result:
        final += " " + words[1]
    return final

def ocr_vision(image_path):
    print(f"processing {image_path}")
    
    if vision:
        output_image = resize_image(image_path, 350)  # downscale the image
        image = load_image(os.path.abspath(output_image))

        response = pipe((
            'Describe the contents of the slide, explain any graphs, images, equations, and text. Transcribe the text.',
            image
        ))

        os.remove(os.path.abspath(output_image))  # remove the downscaled image
        return response.text

def resize_image(image_path, width):
    output_image = image_path.split(".")
    output_image = output_image[0] + "_downscale.png"

    img = Image.open(os.path.abspath(image_path))
    wpercent = (width / float(img.size[0]))
    hsize = int((float(img.size[1]) * float(wpercent)))
    img = img.resize((width, hsize), Image.Resampling.LANCZOS)
    img.save(os.path.abspath(output_image))
    return output_image
