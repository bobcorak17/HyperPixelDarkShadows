from soco.discovery import by_name
import requests
from PIL import Image
from io import BytesIO
import os

# Get the speaker object by zone name
zone = by_name("Basement")
if zone is None:
    raise RuntimeError("Basement zone not found")

# Get track info
track_info = zone.get_current_track_info()
album_art_uri = track_info.get("album_art")

if not album_art_uri:
    raise RuntimeError("No album art available")

# If Sonos returns a relative path, prepend the speaker’s base URL
if album_art_uri.startswith("/"):
    base_url = f"http://{zone.ip_address}:1400"
    album_art_url = base_url + album_art_uri
else:
    album_art_url = album_art_uri

# Fetch and load into PIL
response = requests.get(album_art_url)
response.raise_for_status()

# --- hide pygame banner ---
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
os.environ["SDL_VIDEODRIVER"] = "x11"  # GUI terminal
import pygame

# --- initialize pygame ---
pygame.init()
pygame.mouse.set_visible(False)

# --- open fullscreen surface ---
screen = pygame.display.set_mode((800, 480), pygame.FULLSCREEN)

# --- load JPEG via PIL ---
try:
    img = Image.open(BytesIO(response.content))
    img = img.convert("RGB")
    img = img.resize(screen.get_size())  # scale to fit screen
    data = img.tobytes()
    surf = pygame.image.fromstring(data, img.size, img.mode)
    screen.blit(surf, (0,0))
except Exception as e:
    # fallback: black screen if image fails
    screen.fill((0,0,0))

pygame.display.flip()

# --- keep display ---
pygame.time.wait(5000)  # 5 seconds

pygame.quit()

