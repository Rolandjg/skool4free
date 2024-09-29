import os
from pdf2image import convert_from_path

# Function to convert PDF to images and save them in a directory
def pdf_to_images(pdf_path, output_dir):
    # Check if the output directory exists, if not, create it
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Convert PDF to images
    images = convert_from_path(pdf_path)
    
    # Save each image to the output directory
    for i, image in enumerate(images):
        image_path = os.path.join(output_dir, f'page_{i+1}.png')
        image.save(image_path, 'PNG')
        print(f"Saved {image_path}")

