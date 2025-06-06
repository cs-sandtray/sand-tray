from PIL import Image
import pathlib

BASE_DIR = pathlib.Path(__file__).parent.parent / "static" / "elements"

def white_to_transparent(img_path, output_path, threshold=210):

    img = Image.open(img_path).convert("RGBA")
    datas = img.getdata()

    new_data = []
    for item in datas:
        r, g, b, a = item
        if r > threshold and g > threshold and b > threshold:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append((r, g, b, a))

    img.putdata(new_data)
    img.save(output_path, "PNG")

image_name = "Lotus_Model.png"

white_to_transparent(BASE_DIR / image_name, BASE_DIR / image_name)
