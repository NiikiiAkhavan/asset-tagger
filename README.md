# Asset Tagger

A small Python tool that uses AI to describe and tag game art automatically.

You point it at a folder of game images (sprites). For each image it asks Google Gemini for a short description, a category and a few tags, and saves everything in one `assets.json` file that a game engine or an asset browser can read.

## Why

Game projects have hundreds of images. Tagging them by hand, so people can search "all weapons" or "all wooden props", is slow and boring. If you've done something twice by hand, it should be a script.

## Example output

```json
"shield-rectangle.png": {
  "description": "A curved rectangular shield with blue trim and a central spike.",
  "category": "item",
  "tags": ["shield", "rectangular", "metal", "blue"]
}
```

Categories: `character`, `item`, `wall`, `floor`, `prop`, `ui`, `effect`.

## How to run

Needs Python 3.10 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a file called `.env` with your Gemini API key (free from Google AI Studio):

```
GEMINI_API_KEY=your-key-here
```

Put PNG images in the `sprites/` folder, then run:

```bash
python tagger.py
```

The test images are from Kenney's free "Mini Dungeon" pack (CC0).

## How it works

- Each image is sent to Gemini together with the file name as a hint and a short list of rules (tag spelling, what counts as an item or a wall).
- Gemini is asked to answer in JSON, with `temperature: 0` so the same image gets the same answer.
- Results are saved after every image. Images that are already in `assets.json` are skipped, so a second run is instant and free.
- If Gemini is busy (HTTP 503) or rate-limits (429), the tool waits and retries. If it still fails, it moves on, and the next run only processes the missing images.

## What I learned while building it

- **The first version made clear mistakes.** It called a shield a wall and a spear a magic wand. The AI only saw a small preview image, so I added the file name as a hint. Most mistakes disappeared.
- **Fixing one thing broke another.** After adding the rule "don't repeat the category as a tag", the AI stopped using the object's own name (the coin had no "coin" tag). I added a rule that the first tag is always the object's name.
- **AI answers change between runs.** The same image got different tags each time, so I set `temperature: 0` and made the tool keep results instead of re-tagging.
- **Free AI services are sometimes overloaded**, so retries and saving progress are not optional.

`assets_v1.json`, `assets_v2.json` and `assets.json` show the results before and after each fix.

## What I would improve next

- **A fixed vocabulary for tags.** The AI still mixes "wood" and "wooden", or "rock" and "stones". A small mapping in the code would make search reliable.
- **Do not depend only on file names.** Good names give good tags, but a file called `asset_042.png` gets no help.
- **Load the results in a game engine**, for example a small Godot plugin that shows the tags in the editor.
- **Support more image types** (JPG, WebP) and a command-line option to choose the folder.
