
# Python code example for downloading an image

import requests
import pollinations

def download_image(image_url):
    # Fetching the image from the URL
    response = requests.get(image_url)
    # Writing the content to a file named 'image.jpg'
    with open('image.jpg', 'wb') as file:
        file.write(response.content)
    # Logging completion message
    print('Download Completed')

# Image details
prompt = 'A beautiful landscape'
width = 1024
height = 1024
seed = 42 # Each seed generates a new image variation
model = 'flux' # Using 'flux' as default if model is not provided

image_url = f"https://pollinations.ai/p/{prompt}?width={width}&height={height}&seed={seed}&model={model}"

download_image(image_url)


# Using the pollinations pypi package

## pip install pollinations



model = pollinations.Image(
    model="flux",
    width=1024,
    height=1024,
    seed=42
)

model.Generate(
    prompt="A beautiful landscape",
    save=True
)
