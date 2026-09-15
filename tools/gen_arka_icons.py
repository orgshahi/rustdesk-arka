"""
ARKA placeholder icon generator.
Produces a modern rounded-square teal "A" monogram at the exact sizes/formats
the RustDesk source expects, so branding assets are replaced without breaking
any layout. Temporary placeholder — replace with the official Arka logo later.
"""
import os
from PIL import Image, ImageDraw, ImageFont

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# Fallback: allow override via env
REPO = os.environ.get("ARKA_REPO", REPO)

TEAL_TOP = (20, 184, 166, 255)     # #14B8A6  teal-500
TEAL_BOT = (13, 105, 96, 255)      # #0D6960  deep teal
WHITE = (255, 255, 255, 255)

SS = 4  # supersample factor for crisp downscaling
MASTER = 1024


def rounded_mask(size, radius):
    m = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return m


def vgradient(size, top, bot):
    grad = Image.new("RGBA", (size, size))
    px = grad.load()
    for y in range(size):
        t = y / (size - 1)
        r = int(top[0] * (1 - t) + bot[0] * t)
        g = int(top[1] * (1 - t) + bot[1] * t)
        b = int(top[2] * (1 - t) + bot[2] * t)
        for x in range(size):
            px[x, y] = (r, g, b, 255)
    return grad


def load_font(px):
    for name in ("segoeuib.ttf", "arialbd.ttf", "seguisb.ttf", "arial.ttf"):
        p = os.path.join("C:\\Windows\\Fonts", name)
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, px)
            except Exception:
                pass
    return ImageFont.load_default()


def make_master():
    S = MASTER * SS
    canvas = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    radius = int(S * 0.22)
    tile = vgradient(S, TEAL_TOP, TEAL_BOT)
    mask = rounded_mask(S, radius)
    canvas.paste(tile, (0, 0), mask)

    # White "A" monogram, optically centered
    draw = ImageDraw.Draw(canvas)
    font = load_font(int(S * 0.62))
    txt = "A"
    bbox = draw.textbbox((0, 0), txt, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (S - tw) / 2 - bbox[0]
    y = (S - th) / 2 - bbox[1] - int(S * 0.02)
    draw.text((x, y), txt, font=font, fill=WHITE)

    return canvas.resize((MASTER, MASTER), Image.LANCZOS)


def save_png(master, path, size, mode=None):
    im = master.resize((size, size), Image.LANCZOS)
    if mode == "P":
        im = im.convert("RGBA")  # keep alpha; RGBA is safe for these UI pngs
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)
    return im.size


def save_ico(master, path, sizes):
    im = master.resize((max(sizes) if False else 256, 256), Image.LANCZOS)
    base = master.resize((256, 256), Image.LANCZOS)
    base.save(path, format="ICO", sizes=[(s, s) for s in sorted(sizes)])


def main():
    os.chdir(REPO)
    master = make_master()

    # PNGs (exact original sizes)
    print(save_png(master, "res/icon.png", 1024))
    print(save_png(master, "res/128x128@2x.png", 256))
    print(save_png(master, "res/128x128.png", 128))
    print(save_png(master, "res/64x64.png", 64))
    print(save_png(master, "res/32x32.png", 32))

    # ICOs (exact original size sets)
    save_ico(master, "res/icon.ico", {16, 32, 48, 64, 128})
    save_ico(master, "res/tray-icon.ico", {32})
    save_ico(master, "flutter/windows/runner/resources/app_icon.ico", {48})
    print("ICOs written")

    # Verify
    from PIL import Image as I
    for p in ["res/icon.ico", "res/tray-icon.ico",
              "flutter/windows/runner/resources/app_icon.ico"]:
        im = I.open(p)
        frames = []
        try:
            i = 0
            while True:
                im.seek(i); frames.append(im.size); i += 1
        except EOFError:
            pass
        print(p, im.info.get("sizes"))


if __name__ == "__main__":
    main()
