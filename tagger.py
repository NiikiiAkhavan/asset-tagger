import os
import json
import time
import base64
from pathlib import Path

import requests
from dotenv import load_dotenv

# Read the secret key from the hidden .env file
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent"

SPRITES_FOLDER = Path("sprites")
OUTPUT_FILE = Path("assets.json")


def build_prompt(file_name):
    # The instructions for Gemini. Now they include the file name as a hint.
    # ({{ and }} are just how you write a normal { or } inside an f-string)
    return f"""You are helping a game developer organise their art assets.
The file name is "{file_name}". The artist chose this name, so use it as a strong hint about what the object is.
Look at the image and answer ONLY with JSON in this format:
{{"description": "one short sentence, starting with a capital letter and ending with a period",
 "category": "one of: character, item, wall, floor, prop, ui, effect",
 "tags": ["3 to 5 tags"]}}

Rules for tags:
- the first tag is always the name of the object itself (for example "coin", "key", "shield", "gate")
- lowercase; join words with a hyphen (for example "sci-fi", never "scifi")
- describe the object itself: what it is, its material, colour or use
- do not repeat the category as a tag
- do not use art-style words like "isometric", "low-poly", "voxel" or "3d"

Rules for category:
- item: things a player can pick up or use (weapons, shields, keys, potions, coins); chests and furniture are props
- wall: wall pieces, doors and gates
- floor: ground tiles"""


def tag_image(image_path):
    # A picture can't travel inside a text message, so we turn it into text (base64)
    image_bytes = image_path.read_bytes()
    image_text = base64.b64encode(image_bytes).decode("utf-8")

    # The message: our instructions (with the file name) + the picture
    body = {
        "contents": [{
            "parts": [
                {"text": build_prompt(image_path.name)},
                {"inline_data": {"mime_type": "image/png", "data": image_text}},
            ]
        }],
        "generationConfig": {
            "responseMimeType": "application/json",  # answer in clean JSON
            "temperature": 0,                        # less random: same picture, same answer
        },
    }
    headers = {"x-goog-api-key": API_KEY, "Content-Type": "application/json"}

    # Send it and wait at most 60 seconds
    response = requests.post(URL, headers=headers, json=body, timeout=60)
    response.raise_for_status()  # stop with an error if Gemini said no

    # Take Gemini's answer and turn it into a Python dictionary
    answer_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(answer_text)


def tag_with_retry(image_path, tries=3):
    # Gemini is sometimes busy (503) or says "too fast" (429). Then we wait and try again.
    for attempt in range(1, tries + 1):
        try:
            return tag_image(image_path)
        except requests.exceptions.HTTPError as error:
            busy = error.response.status_code in (429, 503)
            if busy and attempt < tries:
                print("   Gemini is busy, waiting 10 seconds and trying again...")
                time.sleep(10)
            else:
                raise


def main():
    # Load the results from last time, so we don't tag the same picture twice
    if OUTPUT_FILE.exists():
        results = json.loads(OUTPUT_FILE.read_text())
    else:
        results = {}

    images = sorted(SPRITES_FOLDER.glob("*.png"))
    print("Found", len(images), "pictures")

    for image_path in images:
        if image_path.name in results:
            print("Skipping (already done):", image_path.name)
            continue

        print("Tagging:", image_path.name)
        try:
            results[image_path.name] = tag_with_retry(image_path)
        except Exception as error:
            print("   Failed, moving on:", error)
            continue

        # Save after every picture, so nothing is lost if something breaks
        OUTPUT_FILE.write_text(json.dumps(results, indent=2))
        time.sleep(4)  # small pause so the free version doesn't say "too fast"

    print("Done!", len(results), "pictures saved in", OUTPUT_FILE)


main()