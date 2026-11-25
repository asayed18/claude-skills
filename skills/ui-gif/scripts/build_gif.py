"""Build a UI demo GIF from browser screenshots and a JSON scene.

Run: uv run --with pillow python -I build_gif.py scene.json [--width 640]

See SKILL.md for the scene format.
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

DARK = (17, 24, 39)
MUTED = (148, 163, 184)
RING_FILL = (250, 204, 21, 70)
ORANGE = (234, 88, 12)
RED = (239, 68, 68)
ARROW = [(0, 0), (0, 17), (4, 13), (7, 20), (10, 19), (7, 12), (12, 12)]

# (regular file, regular index, bold file, bold index); first one that loads wins.
FONT_CANDIDATES = [
    ("/System/Library/Fonts/HelveticaNeue.ttc", 0, "/System/Library/Fonts/HelveticaNeue.ttc", 1),
    ("/System/Library/Fonts/Helvetica.ttc", 0, "/System/Library/Fonts/Helvetica.ttc", 1),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 0, "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 0),
    ("/usr/share/fonts/TTF/DejaVuSans.ttf", 0, "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf", 0),
    ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 0, "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 0),
    ("C:/Windows/Fonts/arial.ttf", 0, "C:/Windows/Fonts/arialbd.ttf", 0),
]


class Fonts:
    def __init__(self, override):
        self.choice = None
        if override:
            self.choice = (override["regular"], 0, override.get("bold", override["regular"]), 0)
        else:
            for c in FONT_CANDIDATES:
                try:
                    ImageFont.truetype(c[0], 10, index=c[1])
                    ImageFont.truetype(c[2], 10, index=c[3])
                    self.choice = c
                    break
                except OSError:
                    continue
        if self.choice is None:
            print("no system font found, using Pillow's built-in font; set \"font\" in the scene for a better one", file=sys.stderr)

    def get(self, size, bold):
        size = max(8, round(size))
        if self.choice is None:
            return ImageFont.load_default(size)
        path, index = (self.choice[2], self.choice[3]) if bold else (self.choice[0], self.choice[1])
        return ImageFont.truetype(path, size, index=index)


class Builder:
    """Draws at output resolution: screenshots are resized once, and every coordinate,
    line width and font size from the scene is multiplied by the same scale."""

    def __init__(self, base, start, width, fonts):
        self.base = base
        self.target_width = width
        self.fonts = fonts
        self.scale = None
        self.src_size = None
        self.size = None
        self.pos = tuple(start) if start else None
        self.frames = []
        self.durations = []
        self.keyframes = []
        self.cache = {}

    def init_scale(self, src_size):
        self.src_size = src_size
        w = self.target_width or src_size[0]
        if w > src_size[0]:
            print(f"width {w} is larger than the screenshots ({src_size[0]}); the GIF will look soft", file=sys.stderr)
        self.scale = w / src_size[0]
        self.size = (round(src_size[0] * self.scale), round(src_size[1] * self.scale))
        s = self.scale
        self.bar_h = round(44 * s)
        self.ring_r = 18 * s
        self.caption_font = self.fonts.get(17 * s, True)
        self.title_font = self.fonts.get(30 * s, True)
        self.sub_font = self.fonts.get(18 * s, False)

    def image(self, name):
        if name not in self.cache:
            path = Path(name) if Path(name).is_absolute() else self.base / name
            img = Image.open(path).convert("RGB")
            if self.src_size is None:
                self.init_scale(img.size)
            elif img.size != self.src_size:
                sys.exit(f"{name} is {img.size}, the first frame is {self.src_size}; capture all frames at one viewport")
            if img.size != self.size:
                img = img.resize(self.size, Image.LANCZOS)
            self.cache[name] = img
        return self.cache[name]

    def px(self, v):
        return v * self.scale

    def canvas(self):
        w, h = self.size
        return Image.new("RGB", (w, h + self.bar_h), DARK)

    def compose(self, name, caption, pos, box=None, pulse=None):
        img = self.canvas()
        img.paste(self.image(name), (0, 0))
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(overlay)
        lw = lambda w: max(1, round(w * self.scale))
        if box:
            d.rounded_rectangle([self.px(v) for v in box], radius=self.px(8), outline=RED + (255,), width=lw(3))
        if pos:
            x, y = self.px(pos[0]), self.px(pos[1])
            r = self.ring_r
            d.ellipse([x - r, y - r, x + r, y + r], fill=RING_FILL, outline=ORANGE + (255,), width=lw(3))
            if pulse:
                pr, alpha = pulse
                pr = self.px(pr)
                d.ellipse([x - pr, y - pr, x + pr, y + pr], outline=ORANGE + (alpha,), width=lw(4))
            d.polygon([(x + self.px(px), y + self.px(py)) for px, py in ARROW], fill=DARK + (255,), outline=(255, 255, 255, 255))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        if caption:
            d = ImageDraw.Draw(img)
            d.text((self.px(16), self.size[1] + self.bar_h / 2), caption, font=self.caption_font, fill="white", anchor="lm")
        return img

    def add(self, frame, ms, key=False):
        self.frames.append(frame)
        self.durations.append(int(ms))
        if key:
            self.keyframes.append(frame)

    def title(self, heading, sub="", ms=1900):
        img = self.canvas()
        w, h = img.size
        d = ImageDraw.Draw(img)
        d.text((w / 2, h / 2 - self.px(18)), heading, font=self.title_font, fill="white", anchor="mm")
        if sub:
            d.text((w / 2, h / 2 + self.px(22)), sub, font=self.sub_font, fill=MUTED, anchor="mm")
        self.add(img, ms, key=True)

    def hold(self, name, caption, ms, box=None, pos=None):
        if pos:
            self.pos = tuple(pos)
        self.add(self.compose(name, caption, self.pos, box), ms, key=True)

    def move(self, name, caption, to, steps=14, box=None):
        start = self.pos or tuple(to)
        for i in range(1, steps + 1):
            t = i / steps
            t = t * t * (3 - 2 * t)
            p = (start[0] + (to[0] - start[0]) * t, start[1] + (to[1] - start[1]) * t)
            self.add(self.compose(name, caption, p, box), 45)
        self.pos = tuple(to)

    def click(self, name, caption, box=None):
        for i in range(4):
            t = i / 3
            self.add(self.compose(name, caption, self.pos, box, pulse=(18 + 26 * t, int(255 * (1 - t)))), 70)


def first_image(steps):
    for s in steps:
        for k in ("hold", "move", "click"):
            if k in s:
                return s[k]
    sys.exit("scene has no screenshot step")


def contact_sheet(keyframes, out):
    picks = keyframes if len(keyframes) <= 4 else [keyframes[round(i * (len(keyframes) - 1) / 3)] for i in range(4)]
    w, h = picks[0].size
    tw, th = w // 2, h // 2
    sheet = Image.new("RGB", (tw * 2, th * ((len(picks) + 1) // 2)), "white")
    for i, f in enumerate(picks):
        sheet.paste(f.resize((tw, th)), ((i % 2) * tw, (i // 2) * th))
    sheet.save(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scene")
    ap.add_argument("--width", type=int, help="output width in px; overrides the scene's width")
    args = ap.parse_args()

    scene_path = Path(args.scene).resolve()
    scene = json.loads(scene_path.read_text())
    base = scene_path.parent
    b = Builder(base, scene.get("start"), args.width or scene.get("width"), Fonts(scene.get("font")))
    b.image(first_image(scene["steps"]))

    for s in scene["steps"]:
        box = s.get("box")
        if "title" in s:
            b.title(s["title"], s.get("sub", ""), s.get("ms", 1900))
        elif "hold" in s:
            b.hold(s["hold"], s.get("caption", ""), s.get("ms", 900), box, s.get("pos"))
        elif "move" in s:
            b.move(s["move"], s.get("caption", ""), s["to"], s.get("steps", 14), box)
        elif "click" in s:
            b.click(s["click"], s.get("caption", ""), box)
        else:
            sys.exit(f"unknown step: {s}")

    out = Path(scene.get("out", "demo.gif"))
    out = out if out.is_absolute() else base / out
    raw = out.with_name(out.stem + ".raw.gif")
    b.frames[0].save(raw, save_all=True, append_images=b.frames[1:], duration=b.durations, loop=0, disposal=1)
    if shutil.which("ffmpeg"):
        subprocess.run(
            [
                "ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-fps_mode", "passthrough",
                "-filter_complex",
                "[0:v]split[a][b];[a]palettegen=stats_mode=diff:max_colors=128[p];[b][p]paletteuse=dither=none:diff_mode=rectangle",
                str(out),
            ],
            check=True,
        )
        raw.unlink()
    else:
        raw.replace(out)
        print("ffmpeg not found: kept the unreduced Pillow GIF", file=sys.stderr)
    sheet = out.with_name(out.stem + ".sheet.png")
    contact_sheet(b.keyframes, sheet)
    w, h = b.frames[0].size
    total = sum(b.durations) / 1000
    print(f"{out}  {w}x{h}  {len(b.frames)} frames  {total:.1f} s  {out.stat().st_size / 1e6:.2f} MB")
    print(f"{sheet}  check this before sending")


if __name__ == "__main__":
    main()
