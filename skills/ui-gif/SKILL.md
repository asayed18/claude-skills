---
name: ui-gif
description: Make a demo GIF of a web UI change or feature from browser screenshots, in a clear house style - a highlighted ring around the mouse pointer, a click pulse, a red box around the new element, a caption bar under each frame and a title card per change. Use whenever the user asks for a GIF, an animated demo, a screen recording, a walkthrough clip, a before/after animation or a visual for an announcement, release note, PR or chat message about a UI, even if they do not say "skill" or "GIF".
---

# UI demo GIF

A sequence of browser screenshots has no cursor, so on its own it does not show where the click happens or which part of the screen is new. This skill captures a few keyframes and then draws the pointer, its movement, the click pulse, a highlight box, captions and title cards with `scripts/build_gif.py`. Do not inject a fake cursor into the page: drawing it afterwards keeps the app untouched and lets you fix a position without capturing again.

Requirements: a browser tool that saves screenshots as image files, Python with Pillow (`uv run --with pillow` or `pip install pillow`), and `ffmpeg` on the PATH for the final size reduction.

## 1. Open the app

- **Local change:** use the dev server of the checkout that holds the change. When several checkouts or worktrees run dev servers, confirm the port belongs to this one (for example `lsof -iTCP -sTCP:LISTEN -P` and the process's working directory) before capturing.
- **Deployed app:** if it needs a sign-in, ask the user to sign in in the browser you are driving, and continue when they confirm. Never type their credentials.
- In a deployed or production app, do not trigger actions with real effects (sending, ordering, creating records) just for a demo. Open existing records that already show the feature, or use test data, and tell the user which.
- Content inside a cross-origin iframe is often invisible to DOM tools (`find`, accessibility tree). Click it by screenshot coordinates instead.

## 2. Capture keyframes

- Set a viewport that keeps UI text readable at the screenshot size, and keep it fixed: every frame of one GIF must have the same pixel size (the script refuses mixed sizes). Wider than about 1000 CSS px usually makes text too small in an 800 px wide GIF.
- Take one full screenshot per state: the opening screen, the state before each click, and the result. Copy the chosen images into a working folder with short names (`f1.png`, `f2.png`, ...).
- For every frame write down, while you can still see it: the file name, the pointer target in screenshot pixel coordinates, and the box `[x0, y0, x1, y1]` around the new element with 3 to 6 px of padding. Coordinates are in the screenshot's pixels, not CSS pixels.
- Rest the pointer beside or just below its target, not on the text: the ring covers small text.
- **Before/after of a code change:** capture "after", then check out the old version of only the changed files (`git checkout <old-sha> -- <files>`), let hot reload apply it, capture "before", then restore (`git checkout HEAD -- <same files>`). Check `git status` afterwards so nothing stays reverted.
- Reset the viewport when done.

## 3. Write the scene

One scene per change: title card, opening screen, pointer moves, click, result. Write `scene.json` next to the frames:

```json
{
  "out": "demo.gif",
  "start": [400, 250],
  "steps": [
    {"title": "1 · Bulk export", "sub": "Orders list  ·  v2.4"},
    {"hold": "f1.png", "caption": "The orders list", "ms": 800},
    {"move": "f1.png", "caption": "Select the rows to export", "to": [612, 318], "steps": 14, "box": [560, 300, 700, 336]},
    {"click": "f1.png", "caption": "Select the rows to export", "box": [560, 300, 700, 336]},
    {"hold": "f2.png", "caption": "NEW: export the selection as CSV", "ms": 2600, "box": [540, 340, 760, 380]}
  ]
}
```

Step types:
- `title`: a full-frame card, `heading` large and centered, `sub` smaller below it. Default 1.9 s. Use `<n> · <change name>` and `<where>  ·  <version or ticket>`.
- `hold`: a static frame. Optional `pos` jumps the pointer without animation.
- `move`: the pointer travels from its current position to `to`, eased with smoothstep, 45 ms per step.
- `click`: a 4-frame pulse ring at the current pointer position.
- `box` is optional on `hold`, `move` and `click`. Show it from the moment the pointer starts toward the element and keep it through the hold, so the eye lands there first.

Paths are relative to the scene file. `start` is where the pointer begins; leave it out to start at the first `to`. An optional `"font": {"regular": "<path>", "bold": "<path>"}` overrides the font (see below).

Resolution: an optional `"width": 640` sets the GIF's width in pixels (the height follows the screenshots' aspect ratio, plus the caption bar). Without it the GIF keeps the screenshots' width. Write all coordinates in screenshot pixels regardless: the script scales the screenshots, coordinates, ring, line widths and fonts together, so the style keeps its proportions. A smaller width gives a much smaller file (chat apps often cap previews around 600 to 800 px); a width above the screenshots' width only upscales and looks soft, so capture larger instead. `--width` on the command line overrides the scene for one build.

Timing that reads well:
- `steps`: 14 for a normal move, 8 to 10 for a short one, about 20 for a slow sweep along a line of text.
- `ms`: 500 to 900 on a new screen before the pointer moves, 1300 to 1500 on an intermediate state, 2200 to 3000 on the frame that shows the change.
- Captions: one short sentence per step. Start the caption with `NEW:` on the step that shows the change.

## 4. Build and check

```bash
uv run --with pillow python -I <skill-dir>/scripts/build_gif.py <folder>/scene.json
```

The script renders every frame with Pillow, writes the GIF with per-frame durations, reduces it with ffmpeg (`palettegen`/`paletteuse`, usually to about a tenth of the size; without ffmpeg it keeps the larger Pillow file and says so) and writes `<name>.sheet.png`, up to four keyframes tiled.

Open the sheet image and check that the pointer, boxes and captions sit where intended before sending. For a wrong position, fix the coordinates in the scene and rebuild; there is no need to capture again.

Fonts: the script uses Helvetica Neue on macOS, DejaVu Sans or Liberation Sans on Linux, Arial on Windows, and Pillow's built-in font as a last resort. Set `font` in the scene to use another TTF/OTF file.

## 5. Deliver

- Give the user the GIF file (and mention the sheet only if they want to review frames).
- Say which data visible in the GIF is demo or test data and where it came from, so nobody mistakes it for real records.
- To attach it to a chat or announcement draft, upload the file through the tool for that platform and add it to the draft; let the user send it.
