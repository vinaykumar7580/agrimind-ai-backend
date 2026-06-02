from PIL import Image

def get_image_info(image_path):

    img = Image.open(image_path)

    return {
        "width": img.width,
        "height": img.height,
        "format": img.format
    }