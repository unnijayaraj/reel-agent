import os
import io
import requests
from urllib.parse import quote
from dotenv import load_dotenv
import anthropic
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, concatenate_videoclips, vfx

load_dotenv()

# ─────────────────────────────────────────
#  YOUR WEEKLY STATS — edit this each week
# ─────────────────────────────────────────
STATS = {
    "week": "June 16–22",
    "followers_gained": 412,
    "top_post_reach": 84000,
    "top_post_topic": "AI tools for creators",
    "reel_views": 210000,
    "profile_visits": 3100,
    "accounts_reached": 95000,
}

# ─────────────────────────────────────────
#  SETTINGS
# ─────────────────────────────────────────
SLIDES_FOLDER      = "slides"
OUTPUT_FILE        = "reel.mp4"
WIDTH, HEIGHT      = 1080, 1920
SECONDS_PER_SLIDE  = 2.5
FPS                = 30
FONT_PATH          = "/System/Library/Fonts/HelveticaNeue.ttc"
TEXT_COLOR         = (255, 255, 255)
ACCENT             = (180, 100, 255)

POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}?width=1080&height=1920&model=flux&nologo=true"


# ─────────────────────────────────────────
#  STEP 1 — Claude writes slide text + image prompts
# ─────────────────────────────────────────
def generate_slides(stats: dict):
    print("Step 1: Asking Claude to write your slides + image prompts...")

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    prompt = f"""
You are a viral Instagram content writer for a creator who posts data-driven reels.

Here are this week's Instagram analytics:
- Week: {stats['week']}
- New followers: {stats['followers_gained']}
- Top post reach: {stats['top_post_reach']:,} (topic: {stats['top_post_topic']})
- Reel views: {stats['reel_views']:,}
- Profile visits: {stats['profile_visits']:,}
- Accounts reached: {stats['accounts_reached']:,}

Write exactly 7 slides for an Instagram Reel. Each slide is short (max 8 words).
Use line breaks (\\n) to split long slides across 2 lines.

For each slide also write a vivid background image prompt (describe a beautiful,
atmospheric scene that matches the mood of the slide — no text, no people, just scenery/abstract).

Format your response EXACTLY like this, nothing else:
SLIDE 1: [text]
IMAGE 1: [background image prompt]
SLIDE 2: [text]
IMAGE 2: [background image prompt]
SLIDE 3: [text]
IMAGE 3: [background image prompt]
SLIDE 4: [text]
IMAGE 4: [background image prompt]
SLIDE 5: [text]
IMAGE 5: [background image prompt]
SLIDE 6: [text]
IMAGE 6: [background image prompt]
SLIDE 7: [text]
IMAGE 7: [background image prompt]
CAPTION: [1-2 sentence caption with hashtags]

Make slide 1 a strong hook. Make slide 7 a follow CTA.
"""
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text
    slides = []
    image_prompts = []
    caption = ""

    for line in raw.strip().split("\n"):
        line = line.strip()
        if line.startswith("SLIDE") and ":" in line:
            slides.append(line.split(":", 1)[1].strip())
        elif line.startswith("IMAGE") and ":" in line:
            image_prompts.append(line.split(":", 1)[1].strip())
        elif line.startswith("CAPTION") and ":" in line:
            caption = line.split(":", 1)[1].strip()

    print(f"  Got {len(slides)} slides and {len(image_prompts)} image prompts.")
    print(f"  Caption: {caption}\n")
    return slides, image_prompts, caption


# ─────────────────────────────────────────
#  STEP 2 — Pollinations AI generates background images
# ─────────────────────────────────────────
def generate_backgrounds(image_prompts: list[str]) -> list[Image.Image]:
    print("Step 2: Generating AI backgrounds with Pollinations (free)...")

    backgrounds = []

    for i, prompt in enumerate(image_prompts):
        print(f"  Generating image {i+1}/{len(image_prompts)}: {prompt[:60]}...")

        url = POLLINATIONS_URL.format(prompt=quote(prompt))
        response = requests.get(url, timeout=90)

        if response.status_code == 200 and response.headers.get("content-type", "").startswith("image"):
            img = Image.open(io.BytesIO(response.content)).convert("RGB")
            img = _fill_portrait(img)
            backgrounds.append(img)
            print(f"    Done.")
        else:
            print(f"    Error {response.status_code} — using gradient fallback.")
            backgrounds.append(_make_gradient_fallback())

    print()
    return backgrounds


def _fill_portrait(img: Image.Image) -> Image.Image:
    """Resize and center-crop image to exactly 1080x1920."""
    target_w, target_h = WIDTH, HEIGHT
    src_w, src_h = img.size

    scale = max(target_w / src_w, target_h / src_h)
    new_w = int(src_w * scale)
    new_h = int(src_h * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)

    left = (new_w - target_w) // 2
    top  = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


def _make_gradient_fallback() -> Image.Image:
    """Dark purple gradient used if HF API fails for a slide."""
    img = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(15  + (40  - 15)  * t)
        g = int(15  + (10  - 15)  * t)
        b = int(30  + (60  - 30)  * t)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))
    return img


# ─────────────────────────────────────────
#  STEP 3 — Pillow overlays text on each background
# ─────────────────────────────────────────
def render_slides(slides: list[str], backgrounds: list[Image.Image]) -> list[str]:
    print("Step 3: Overlaying text on images...")
    os.makedirs(SLIDES_FOLDER, exist_ok=True)

    saved = []
    total = len(slides)
    for i, (text, bg) in enumerate(zip(slides, backgrounds)):
        path = _draw_slide(text, bg, i + 1, total)
        saved.append(path)
        print(f"  Saved: {path}")

    print()
    return saved


def _draw_slide(text: str, bg: Image.Image, slide_num: int, total: int) -> str:
    img = bg.copy()
    draw = ImageDraw.Draw(img)

    # Dark overlay so text stays readable over any background
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 140))
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    try:
        font_main  = ImageFont.truetype(FONT_PATH, 90)
        font_small = ImageFont.truetype(FONT_PATH, 40)
    except Exception:
        font_main  = ImageFont.load_default()
        font_small = font_main

    # Slide counter (top right)
    draw.text((WIDTH - 140, 80), f"{slide_num}/{total}", font=font_small, fill=(200, 200, 220))

    # Accent bar (left side)
    draw.rectangle([(80, HEIGHT // 2 - 200), (90, HEIGHT // 2 + 200)], fill=ACCENT)

    # Main text (centered)
    lines = text.strip().split("\\n")
    line_h = 110
    y_start = (HEIGHT - len(lines) * line_h) // 2
    for j, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font_main)
        x = (WIDTH - (bbox[2] - bbox[0])) // 2
        draw.text((x, y_start + j * line_h), line, font=font_main, fill=TEXT_COLOR)

    # Progress dots (bottom)
    for d in range(total):
        cx = (WIDTH // 2) - (total * 30 // 2) + d * 30 + 15
        color = ACCENT if (d + 1) == slide_num else (80, 80, 100)
        draw.ellipse([(cx - 8, HEIGHT - 128), (cx + 8, HEIGHT - 112)], fill=color)

    path = f"{SLIDES_FOLDER}/slide_{slide_num:02d}.png"
    img.save(path)
    return path


# ─────────────────────────────────────────
#  STEP 4 — MoviePy stitches slides into MP4
# ─────────────────────────────────────────
def create_video(image_paths: list[str]) -> str:
    print("Step 4: Creating video...")

    clips = [
        ImageClip(p).with_duration(SECONDS_PER_SLIDE).with_effects([vfx.FadeIn(0.3)])
        for p in image_paths
    ]
    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(OUTPUT_FILE, fps=FPS, codec="libx264", audio=False, logger=None)

    print(f"  Video saved: {OUTPUT_FILE} ({final.duration:.1f}s)\n")
    return OUTPUT_FILE


# ─────────────────────────────────────────
#  STEP 5 — Commit and push reel to GitHub
# ─────────────────────────────────────────
def push_to_github(video_path: str, caption: str):
    import subprocess
    from datetime import date

    print("Step 5: Pushing to GitHub...")

    today = date.today().strftime("%Y-%m-%d")
    commit_msg = f"reel {today}"

    commands = [
        ["git", "add", video_path],
        ["git", "commit", "-m", commit_msg],
        ["git", "push"],
    ]

    for cmd in commands:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  Git error: {result.stderr.strip()}")
            return
        print(f"  {' '.join(cmd)} — OK")

    print(f"  Pushed! Caption for today:\n  {caption}\n")


# ─────────────────────────────────────────
#  PIPELINE — runs all 5 steps in order
# ─────────────────────────────────────────
def run_pipeline(stats: dict):
    print("=" * 45)
    print("   AI REEL PIPELINE STARTING")
    print("=" * 45 + "\n")

    slides, image_prompts, caption = generate_slides(stats)   # Step 1
    backgrounds = generate_backgrounds(image_prompts)          # Step 2
    image_paths = render_slides(slides, backgrounds)           # Step 3
    video_path  = create_video(image_paths)                    # Step 4
    push_to_github(video_path, caption)                        # Step 5

    print("=" * 45)
    print("   DONE!")
    print("=" * 45)
    print(f"\nVideo:   {video_path}")
    print(f"Caption: {caption}")


if __name__ == "__main__":
    run_pipeline(STATS)
