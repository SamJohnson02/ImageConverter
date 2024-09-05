from flask import Flask, render_template, request
import os
import requests
from PIL import Image
import pyheif
from config import CLIENT_ID

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    # Define allowed image extensions
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.heic'}

    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename)[1].lower()

    if ext not in allowed_extensions:
        return "Unsupported file type", 400

    try:
        # Handle .heic files
        if ext == '.heic':
            heif_file = pyheif.read(file_path)
            img = Image.frombytes(
                heif_file.mode,
                heif_file.size,
                heif_file.data,
                "raw",
                heif_file.mode,
                heif_file.stride,
            )
        else:
            # Open and process other image formats
            with Image.open(file_path) as img:
                img = img.convert('RGB')
        
        # Resize the image
        img = img.resize((1024, 1024), Image.LANCZOS)

        # Save the image with .jpg extension
        base_filename = os.path.splitext(filename)[0]
        new_filename = base_filename + '.jpg'
        new_file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)

        # Ensure the destination directory exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        # Compress and save the image
        img.save(new_file_path, 'JPEG', quality=85)
        max_size_kb = 500
        quality = 85
        while os.path.getsize(new_file_path) > max_size_kb * 1024:
            # Reduce quality until under the size limit
            quality -= 5
            img.save(new_file_path, 'JPEG', quality=quality)
            if quality <= 10:
                break

        # Upload the image
        headers = {'Authorization': f'Client-ID {CLIENT_ID}'}
        with open(new_file_path, 'rb') as img_file:
            response = requests.post(
                "https://api.imgur.com/3/upload",
                headers=headers,
                files={'image': img_file}
            )

        # Check if the upload was successful
        if response.status_code == 200:
            img_url = response.json()['data']['link']
            img_url = img_url.rsplit('.', 1)[0] + '.jpg'
            print(f"Uploaded {new_filename} to {img_url}")
            return render_template('result.html', image_url=img_url)
        else:
            print(f"Failed to upload {new_filename}: {response.status_code} {response.text}")
            return "Failed to upload image", 500

    except Exception as e:
        print(f"Failed to process image {filename}: {e}")
        return "Error processing image", 500

if __name__ == '__main__':
    app.run(debug=True)
