from PIL import Image, ImageEnhance, ImageOps

def make_nightscape_sky_bright(input_path, output_path):
    # 1) Open & convert to RGB
    img = Image.open(input_path).convert("RGB")

    # 2) Slightly darken (not too much)
    enhancer = ImageEnhance.Brightness(img)
    img_dark = enhancer.enhance(0.5)  # Try 0.5 or 0.6

    # 3) Add a bluish tint
    r, g, b = img_dark.split()
    r = r.point(lambda i: i * 0.8)
    g = g.point(lambda i: i * 0.9)
    b = b.point(lambda i: i * 1.2)
    tinted = Image.merge("RGB", (r, g, b))

    # 4) Create a silhouette (buildings black, sky white)
    gray = tinted.convert("L")
    threshold = 130
    silhouette = gray.point(lambda x: 0 if x < threshold else 255, 'L')  # building=black, sky=white
    silhouette_rgb = silhouette.convert("RGB")

    # 5) If you want to lighten the sky more, create a "bright sky" version of tinted
    bright_enh = ImageEnhance.Brightness(tinted)
    tinted_bright = bright_enh.enhance(1.3)  # Increase factor for a brighter sky

    # 6) Composite: 
    #    Where silhouette is black => building => keep silhouette
    #    Where silhouette is white => sky => use tinted_bright
    #    So we pass silhouette as the mask to keep tinted_bright in the white areas, silhouette_rgb in the black areas
    img_night = Image.composite(silhouette_rgb, tinted_bright, silhouette)

    img_night.save(output_path)
    print(f"Saved bright-sky nightscape to {output_path}")
