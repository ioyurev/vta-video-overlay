from PIL import Image, ImageDraw, ImageFont

from vta_video_overlay.__version__ import __version__

img = Image.new("RGB", (800, 400), (255, 255, 255))
icon = Image.open("../assets/icon.png")
icon = icon.resize((300, 300))
img.paste(icon, (50, 50))
draw = ImageDraw.Draw(img)
font = ImageFont.truetype("arial.ttf", 60)
font2 = ImageFont.truetype("arial.ttf", 40)
draw.text(
    (400, 200),
    f"VTA\nvideo overlay\nv{__version__}",
    font=font,
    fill=(0, 0, 0),
    anchor="lm",
)
draw.text((800, 400), "Loading...", font=font2, fill=(0, 0, 0), anchor="rd")
img.save("splash.png")
