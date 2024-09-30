import os
from pdf2image import convert_from_path

def pdf_to_images(pdf_path, output_dir):
    """Convert PDF to images and save them in a directory."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Convert PDF to images
    images = convert_from_path(pdf_path)
    
    # Save each image to the output directory
    for i, image in enumerate(images):
        image_path = os.path.join(output_dir, f'page_{i+1}.png')
        image.save(image_path, 'PNG')
        print(f"Saved {image_path}")
