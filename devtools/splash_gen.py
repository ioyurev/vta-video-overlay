from PIL import Image, ImageDraw, ImageFont, ImageFile

from vta_video_overlay.__version__ import __version__

img = Image.new("RGB", (800, 400), (255, 255, 255))
icon_file: ImageFile.ImageFile = Image.open("../assets/icon.png")
icon = icon_file.resize((300, 300))
img.paste(icon, (50, 50))
draw = ImageDraw.Draw(img)
PILFONT: ImageFont.FreeTypeFont | ImageFont.ImageFont
PILFONTSMALL: ImageFont.FreeTypeFont | ImageFont.ImageFont
try:
    PILFONT = ImageFont.truetype("times.ttf", 60)
    PILFONTSMALL = ImageFont.truetype("times.ttf", 40)
except Exception as _:
    try:
        PILFONT = ImageFont.truetype("DejaVuSerif.ttf", 60)
        PILFONTSMALL = ImageFont.truetype("DejaVuSerif.ttf", 40)
    except Exception as _:
        PILFONT = ImageFont.load_default(size=60)
        PILFONTSMALL = ImageFont.load_default(size=40)
draw.text(
    (400, 200),
    f"VTA\nvideo overlay\nv{__version__}",
    font=PILFONT,
    fill=(0, 0, 0),
    anchor="lm",
)
draw.text((800, 400), "Loading...", font=PILFONTSMALL, fill=(0, 0, 0), anchor="rd")
img.save("splash.png")
