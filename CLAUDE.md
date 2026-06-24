# Firefly Reel Agent

## Who I am
I am a content creator building an automated Instagram reel system using Python and AI tools.

## What we already built (in ~/pythonPOC1)
A full reel pipeline with 4 steps:
1. `step1_data.py` — structure weekly Instagram stats
2. `step2_script.py` — Claude API generates 7 slide scripts + caption
3. `step3_images.py` — Pillow renders text on gradient backgrounds → PNG slides
4. `step4_video.py` — MoviePy stitches PNGs into an MP4 reel
5. `reel_pipeline.py` — single file that runs all 4 steps end to end

The pipeline is also scheduled as a cloud agent (Claude routine) that runs every Monday 9am and commits reel.mp4 to GitHub repo: https://github.com/unnijayaraj/ai-agent-content

## What this new project does
Upgrade the pipeline by replacing plain gradient backgrounds with Adobe Firefly AI-generated images.

New flow:
- Claude generates slide text AND an image prompt per slide
- Adobe Firefly API generates a custom background image for each slide
- Pillow overlays bold white text on the Firefly image
- MoviePy stitches into final MP4

## API Keys (stored in .env — never commit this file)
- ANTHROPIC_API_KEY — Anthropic Claude API
- ADOBE_CLIENT_ID — Adobe Firefly API
- ADOBE_CLIENT_SECRET — Adobe Firefly API

## Tech stack
- Python 3.14
- anthropic, python-dotenv, Pillow, moviepy
- Adobe Firefly Services API (text-to-image)

## Style preferences
- Teach step by step — I am a content creator learning Python automation
- Run scripts inside the chat when possible
- Keep code simple and well-labelled
- Instagram Reel dimensions: 1080x1920 (9:16)