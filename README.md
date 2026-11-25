# claude-skills

Agent skills for Claude Code and other tools that read the `SKILL.md` format.

| Skill | What it does |
|---|---|
| [ui-gif](skills/ui-gif/SKILL.md) | Turns a few browser screenshots into a demo GIF of a UI change: a highlighted ring around the pointer, a click pulse, a red box on the new element, a caption bar and a title card per change. |

## Install

### As a Claude Code plugin

Each skill is its own plugin, so you install only the skills you pick. In Claude Code, add this repository as a plugin marketplace once, then install a skill by its name:

```
/plugin marketplace add asayed18/claude-skills
/plugin install ui-gif@asayed18
```

The same from a terminal:

```bash
claude plugin marketplace add asayed18/claude-skills
claude plugin install ui-gif@asayed18
```

`/plugin` without arguments lists every skill in the marketplace to pick from. Update later with `/plugin marketplace update asayed18`. Plugin skills are namespaced, so the skill shows up as `ui-gif:ui-gif`.

### By copying the folder

```bash
git clone https://github.com/asayed18/claude-skills.git
cp -R claude-skills/skills/ui-gif ~/.claude/skills/
```

For a single project, copy it into that project's `.claude/skills/` instead.

### As a packaged skill

Each release attaches a packaged `.skill` file for apps that install skills from an uploaded file.

## ui-gif

![ui-gif demo: a pointer with a highlighted ring clicks the Google search box, a red box marks the new element, and a caption bar explains each step](docs/ui-gif-demo.gif)

Built by the skill from three screenshots of google.com, at `--width 720` (0.28 MB).

Ask for a GIF, an animated demo or a before/after clip of a web UI. The skill guides the agent through four steps:

1. Capture keyframes in the browser.
2. Note pointer targets and highlight boxes in screenshot coordinates.
3. Write a short `scene.json`.
4. Run the build script.

```bash
uv run --with pillow python -I <skill-dir>/scripts/build_gif.py scene.json --width 640
```

Requirements: Python with Pillow, and `ffmpeg` on the `PATH` to shrink the result (optional; without it the GIF is larger). Fonts fall back across macOS, Linux and Windows, or set one in the scene.

The script writes the GIF and a `.sheet.png` of up to four keyframes for a quick visual check. See [ui-gif/SKILL.md](skills/ui-gif/SKILL.md) for the scene format, timings and style.

## Adding a skill

Each skill folder under `skills/` is a self-contained plugin:

```
skills/<name>/
├── SKILL.md
├── .claude-plugin/plugin.json   # name, version, "skills": ["./"]
├── assets/icon.png              # square PNG, 512 to 2048 px
└── scripts/ ...                 # optional
```

Add the folder, then one entry to `.claude-plugin/marketplace.json` with `"source": "./skills/<name>"`, a row to the table above, and an install line. Check with `claude plugin validate .` and `claude plugin validate skills/<name>`.

## License

[MIT](LICENSE)
