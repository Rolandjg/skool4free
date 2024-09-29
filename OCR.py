import easyocr

def ocr(image_path, language):
    # Create an OCR reader object
    reader = easyocr.Reader(['en'])

    result = reader.readtext(image_path)
    final = ""
    
    for words in result:
        final += " "+words[1]
    
    print(final)
    return final

if __name__ == "__main__":
    print(ocr("tests/hand_writing.png", 'en'))
