import os
import random
from flask import Flask, jsonify, send_from_directory, url_for, render_template_string
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Retrieve the IMAGE_DIR value from the environment.
# Ensure that the path is correct and respects case (e.g. "Pictures" vs "pictures").
IMAGE_DIR = os.getenv('IMAGE_DIR')
if not IMAGE_DIR:
    app.logger.error("IMAGE_DIR environment variable is not set!")
else:
    app.logger.info("Using IMAGE_DIR: %s", IMAGE_DIR)

# --- Updated Helper Function: Recursive scan ---
def list_image_files(directory):
    """
    Recursively walk through the directory and subdirectories,
    returning a list of image file paths (relative to the given directory).
    """
    allowed_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')
    image_files = []
    for root, _, files in os.walk(directory):
        for f in files:
            if f.lower().endswith(allowed_extensions):
                # Get the file path relative to the base IMAGE_DIR
                rel_path = os.path.relpath(os.path.join(root, f), directory)
                image_files.append(rel_path)
    app.logger.info("Found %d images in %s", len(image_files), directory)
    return image_files

# --- Backend API Endpoint ---
@app.route('/api/random-images', methods=['GET'])
def random_images():
    images = list_image_files(IMAGE_DIR)
    if not images:
        app.logger.error("No images found in %s", IMAGE_DIR)
        return jsonify([])

    count = random.randint(1, 5)
    if len(images) >= count:
        selected = random.sample(images, count)
    else:
        selected = images

    # Build absolute URLs for each image using the /images route.
    image_urls = [url_for('get_image', filename=filename, _external=True) for filename in selected]
    return jsonify(image_urls)

# --- Route to Serve Images ---
@app.route('/images/<path:filename>')
def get_image(filename):
    return send_from_directory(IMAGE_DIR, filename)

# --- Frontend HTML & JavaScript ---
FRONTEND_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Random Photo Mosaic</title>
  <style>
    html, body {
      margin: 0;
      padding: 0;
      overflow: hidden;
      background-color: #000;
      height: 100%;
      width: 100%;
    }
    #photoContainer {
      position: relative;
      width: 100vw;
      height: 100vh;
    }
    #photoContainer img {
      position: absolute;
      object-fit: contain;
      user-select: none;
      -webkit-user-drag: none;
    }
  </style>
</head>
<body>
  <div id="photoContainer"></div>
  <script>
    // Predefined layout templates based on the number of images.
    const layouts = {
      1: [
        [
          { left: "0%", top: "0%", width: "100%", height: "100%" }
        ]
      ],
      2: [
        [
          { left: "0%", top: "0%", width: "50%", height: "100%" },
          { left: "50%", top: "0%", width: "50%", height: "100%" }
        ],
        [
          { left: "0%", top: "0%", width: "100%", height: "50%" },
          { left: "0%", top: "50%", width: "100%", height: "50%" }
        ]
      ],
      3: [
        [
          { left: "0%", top: "0%", width: "60%", height: "100%" },
          { left: "60%", top: "0%", width: "40%", height: "50%" },
          { left: "60%", top: "50%", width: "40%", height: "50%" }
        ],
        [
          { left: "0%", top: "0%", width: "100%", height: "60%" },
          { left: "0%", top: "60%", width: "50%", height: "40%" },
          { left: "50%", top: "60%", width: "50%", height: "40%" }
        ]
      ],
      4: [
        [
          { left: "0%", top: "0%", width: "50%", height: "50%" },
          { left: "50%", top: "0%", width: "50%", height: "50%" },
          { left: "0%", top: "50%", width: "50%", height: "50%" },
          { left: "50%", top: "50%", width: "50%", height: "50%" }
        ]
      ],
      5: [
        [
          { left: "0%", top: "0%", width: "50%", height: "50%" },
          { left: "50%", top: "0%", width: "50%", height: "50%" },
          { left: "0%", top: "50%", width: "33.33%", height: "50%" },
          { left: "33.33%", top: "50%", width: "33.33%", height: "50%" },
          { left: "66.66%", top: "50%", width: "33.33%", height: "50%" }
        ],
        [
          { left: "0%", top: "0%", width: "100%", height: "60%" },
          { left: "0%", top: "60%", width: "25%", height: "40%" },
          { left: "25%", top: "60%", width: "25%", height: "40%" },
          { left: "50%", top: "60%", width: "25%", height: "40%" },
          { left: "75%", top: "60%", width: "25%", height: "40%" }
        ]
      ]
    };

    const container = document.getElementById('photoContainer');

    // Function to fetch images from the API and update the layout.
    async function fetchAndDisplayImages() {
      try {
        const response = await fetch('/api/random-images');
        const imageUrls = await response.json();
        const count = imageUrls.length;
        // If no images are returned, clear the container (or show a message if desired)
        if (count === 0) {
          container.innerHTML = '<p style="color: white; text-align:center;">No images found</p>';
          return;
        }
        // Select a random layout for the given count
        const templates = layouts[count] || layouts[1];
        const layout = templates[Math.floor(Math.random() * templates.length)];
        
        // Clear any existing images
        container.innerHTML = '';
        // Create and position each image element based on the chosen layout
        imageUrls.forEach((url, index) => {
          const img = document.createElement('img');
          img.src = url;
          const pos = layout[index];
          img.style.left = pos.left;
          img.style.top = pos.top;
          img.style.width = pos.width;
          img.style.height = pos.height;
          container.appendChild(img);
        });
      } catch (err) {
        console.error('Error fetching images:', err);
      }
    }

    // Initial load and then refresh every 30 seconds
    fetchAndDisplayImages();
    setInterval(fetchAndDisplayImages, 30000);
  </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(FRONTEND_HTML)

# --- Run Method ---
def run():
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    run()

