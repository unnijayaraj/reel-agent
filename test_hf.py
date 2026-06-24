import requests
from urllib.parse import quote

print("Testing Pollinations AI (free, no key needed)...")

prompt = "glowing purple galaxy background, deep space, vertical portrait style"
url = f"https://image.pollinations.ai/prompt/{quote(prompt)}?width=1080&height=1920&model=flux&nologo=true"

response = requests.get(url, timeout=60)

if response.status_code == 200 and response.headers.get("content-type", "").startswith("image"):
    with open("test_image.png", "wb") as f:
        f.write(response.content)
    print(f"Success! Image saved as test_image.png ({len(response.content)//1024} KB)")
else:
    print(f"Error {response.status_code}: {response.text[:200]}")
