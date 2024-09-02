import os
import requests
from PIL import Image
from config import CLIENT_ID, source_directory, destination_directory

def resize_image(image, size=(1024, 1024)):
    """
    Resize the image to fit within the target size of 1024x1024 pixels.
    """
    image = image.resize(size, Image.LANCZOS)
    return image

def compress_image(image, output_path, max_size_kb, quality=85):
    """
    Compress the image by reducing quality until it's under the max_size_kb.
    """
    image.save(output_path, 'JPEG', quality=quality)
    
    # Check the file size
    while os.path.getsize(output_path) > max_size_kb * 1024 and quality > 10:
        # Reduce the quality and save again
        quality -= 5
        image.save(output_path, 'JPEG', quality=quality)

def convert_and_process_images(source_dir, dest_dir, max_size_kb=500):
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    headers = {'Authorization': f'Client-ID {CLIENT_ID}'}
    
    # Define allowed image extensions
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.xml'}
    
    for filename in os.listdir(source_dir):
        if not any(filename.lower().endswith(ext) for ext in allowed_extensions):
            # Skip non-image files
            continue
        
        file_path = os.path.join(source_dir, filename)
        try:
            with Image.open(file_path) as img:
                # Resize the image to 1024x1024 pixels
                img = resize_image(img)
                
                # Convert to RGB and save the image
                img = img.convert('RGB')
                
                base_filename = os.path.splitext(filename)[0]
                new_filename = base_filename + '.JPG'
                new_file_path = os.path.join(dest_dir, new_filename)

                # Convert and compress the image
                compress_image(img, new_file_path, max_size_kb)
                
                # Upload the image (adjust URL and headers if needed for EPS Fantasy)
                with open(new_file_path, 'rb') as img_file:
                    response = requests.post(
                        "https://api.imgur.com/3/upload",  # Replace with EPS Fantasy upload URL
                        headers=headers,
                        files={'image': img_file}
                    )
                
                # Check if the upload was successful
                if response.status_code == 200:
                    img_url = response.json()['data']['link']
                    print(f"Uploaded {new_filename} to {img_url}")
                else:
                    print(f"Failed to upload {new_filename}: {response.status_code} {response.text}")

                # Confirm that the file was saved
                if os.path.exists(new_file_path):
                    print(f"Saved {new_filename} to {new_file_path}")
                else:
                    print(f"Failed to save {new_filename}")

        except Exception as e:
            print(f"Failed to convert, compress, or upload {filename}: {e}")

# Call the conversion and processing function
convert_and_process_images(source_directory, destination_directory)
