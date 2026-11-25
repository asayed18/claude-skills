# claude-skills

Agent skills for Claude Code and other tools that read the `SKILL.md` format.

| Skill | What it does |
|---|---|
| [ui-gif](ui-gif/SKILL.md) | Turns a few browser screenshots into a demo GIF of a UI change: a highlighted ring around the pointer, a click pulse, a red box on the new element, a caption bar and a title card per change. |

## Install

Copy a skill folder into your personal skills directory:

```bash
git clone https://github.com/asayed18/claude-skills.git
cp -R claude-skills/ui-gif ~/.claude/skills/
```

For a single project, copy it into that project's `.claude/skills/` instead. Each release also attaches a packaged `.skill` file per skill.

## ui-gif

Ask for a GIF, an animated demo or a before/after clip of a web UI. The skill guides the agent through four steps:

1. Capture keyframes in the browser.
2. Note pointer targets and highlight boxes in screenshot coordinates.
3. Write a short `scene.json`.
4. Run the build script.

```bash
uv run --with pillow python -I ~/.claude/skills/ui-gif/scripts/build_gif.py scene.json --width 640
```

Requirements: Python with Pillow, and `ffmpeg` on the `PATH` to shrink the result (optional; without it the GIF is larger). Fonts fall back across macOS, Linux and Windows, or set one in the scene.

The script writes the GIF and a `.sheet.png` of up to four keyframes for a quick visual check. See [ui-gif/SKILL.md](ui-gif/SKILL.md) for the scene format, timings and style.

## License

[MIT](LICENSE)
