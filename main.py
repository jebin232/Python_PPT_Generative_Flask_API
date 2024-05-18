from flask import Flask, request, send_file, render_template
from pptx import Presentation
from pptx.util import Inches
import io
import google.generativeai as genai

app = Flask(__name__)

# Google Gemini API Key Configuration
gemini_api_key = "AIzaSyAtPkrzg6fNBVGhtnJS5ahri0z3WZQQS3Q"
genai.configure(api_key=gemini_api_key)

def generate_text_from_title(title):
    model = genai.GenerativeModel('gemini-pro')
    
    response = model.generate_content(
        f"{title}",
        generation_config=genai.types.GenerationConfig(
            candidate_count=1,
            stop_sequences=['space'],
            max_output_tokens=1000,
            temperature=0.7
        )
    )
    
    return response.text

import requests
from PIL import Image
from io import BytesIO
import random

def get_random_image_url():
    # Replace this with your preferred image search API or URL
    # For demonstration, I'll use Unsplash API
    response = requests.get('https://source.unsplash.com/random')
    return response.url

def download_and_resize_image(image_url, target_width, target_height):
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    img.thumbnail((target_width, target_height))
    
    # Convert the image to RGB mode if it's not already
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    return img

def add_image_to_slide(slide, image_data, left, bottom, width, height):
    left_inch = Inches(left)
    bottom_inch = Inches(bottom)
    width_inch = Inches(width)
    height_inch = Inches(height)
    
    image_stream = BytesIO()
    image_data.save(image_stream, format='PNG')  # Save the image to a stream in PNG format
    image_stream.seek(0)  # Reset the stream position to the beginning
    
    slide.shapes.add_picture(image_stream, left_inch, bottom_inch - height_inch, width_inch, height_inch)


def create_presentation(title, contents):
    prs = Presentation()
    content = contents.replace('*', '')


    # Title Slide
    slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(slide_layout)
    title_placeholder = slide.shapes.title
    title_placeholder.text = title

    # Split content into paragraphs
    paragraphs = content.split('\n')

    # Add a new slide for each paragraph
    for paragraph in paragraphs:
        if paragraph.strip():  # Only add slide for non-empty paragraphs
            slide_layout = prs.slide_layouts[1]
            slide = prs.slides.add_slide(slide_layout)
            title_placeholder = slide.shapes.title
            # title_placeholder.text = 'Content'
            content_placeholder = slide.placeholders[1]
            content_placeholder.text = paragraph

            # Add images randomly on left and right sides
            left_image_url = get_random_image_url()
            right_image_url = get_random_image_url()

            left_image = download_and_resize_image(left_image_url, 200, 200)
            right_image = download_and_resize_image(right_image_url, 200, 200)

            left = random.choice([0, 1])  # 0 for left, 1 for right
            if left == 0:
                    add_image_to_slide(slide, left_image, 0.5, 6.0, 2, 2)  # Adjust bottom value
                    add_image_to_slide(slide, right_image, 6.5, 6.0, 2, 2)  # Adjust bottom value
            else:
                    add_image_to_slide(slide, right_image, 0.5, 6.0, 2, 2)  # Adjust bottom value
                    add_image_to_slide(slide, left_image, 6.5, 6.0, 2, 2)  # Adjust bottom value

    return prs


@app.route('/ppt', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        title = request.form['title']
        content = generate_text_from_title(title)
        prs = create_presentation(title, content)
        
        # Save presentation to a BytesIO stream
        ppt_io = io.BytesIO()
        prs.save(ppt_io)
        ppt_io.seek(0)
        
        return send_file(
                    ppt_io, 
                    download_name='presentation.pptx', 
                    as_attachment=True, 
                    mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation'
                )
        
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)