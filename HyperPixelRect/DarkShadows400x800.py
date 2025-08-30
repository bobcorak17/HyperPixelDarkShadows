#!/usr/bin/env python3
# DarkShadows.py — HyperPixel Day/Night Terminator (400x800 image, centered)

import os, sys
from datetime import datetime, timezone
from PIL import Image
import ephem

# --- Environment vars to suppress banner and tweak pygame ---
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
os.environ.setdefault("SDL_VIDEO_ALLOW_SCREENSAVER", "0")
os.environ["SDL_VIDEO_WINDOW_POS"] = "0,0"
import pygame

# -----------------------------
# Configuration
# -----------------------------
DAY_IMAGE_PATH   = "day.jpg"     # 400x800
NIGHT_IMAGE_PATH = "night.jpg"   # 400x800
UPDATE_INTERVAL  = 60_000        # ms

CITIES = {
    "Null Island": (0.0, 0.0),
    "Tokyo": (35.6895, 139.6917),
    "Stockholm": (59.3293, 18.0686),
    "Honolulu": (21.3069, -157.8583),
    "NYC": (40.7128, -74.0060),
    "LA": (34.0522, -118.2437),
    "Tierra del Fuego": (-54.8019, -68.3029),
    "Sidney": (-33.8651, 151.2099),
}

# -----------------------------
# Helper functions
# -----------------------------
def is_day(lat, lon, now):
    obs = ephem.Observer()
    obs.date = now
    obs.lat = str(lat)
    obs.lon = str(lon)
    sun = ephem.Sun(obs)
    return sun.alt > 0

def latlon_to_xy(lat, lon, img_w, img_h):
    """Convert lat/lon to pixel coords in the image."""
    x = int((lon + 180.0) / 360.0 * img_w)
    y = int((90.0 - lat) / 180.0 * img_h)
    return x, y

def draw_cross(surface, x, y, color=(255, 0, 0), size=5):
    pygame.draw.line(surface, color, (x - size, y), (x + size, y), 2)
    pygame.draw.line(surface, color, (x, y - size), (x, y + size), 2)

def overlay_city_markers(surface, img_w, img_h, screen_w, screen_h):
    """Draw city markers centered on screen with black bars if needed."""
    offset_x = (screen_w - img_w) // 2
    offset_y = (screen_h - img_h) // 2
    for name, (lat, lon) in CITIES.items():
        x_img, y_img = latlon_to_xy(lat, lon, img_w, img_h)
        x_screen = x_img + offset_x
        y_screen = y_img + offset_y
        draw_cross(surface, x_screen, y_screen)

def generate_terminator_image(day_img, night_img):
    now = datetime.now(timezone.utc)
    w, h = day_img.size
    mask = Image.new("1", (w, h))
    for y in range(h):
        lat = 90 - (y / h) * 180.0
        for x in range(w):
            lon = (x / w) * 360.0 - 180.0
            mask.putpixel((x, y), 1 if is_day(lat, lon, now) else 0)
    comp = Image.composite(day_img, night_img, mask)
    return comp

# -----------------------------
# Main
# -----------------------------
pygame.init()
screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
pygame.mouse.set_visible(False)
SCREEN_SIZE = screen.get_size()

# Load 400x800 images
day_img   = Image.open(DAY_IMAGE_PATH).convert("RGB")
night_img = Image.open(NIGHT_IMAGE_PATH).convert("RGB")
img_w, img_h = day_img.size

# Pre-blit black screen
screen.fill((0,0,0))
pygame.display.flip()

# Timer-based updates
pygame.time.set_timer(pygame.USEREVENT, UPDATE_INTERVAL)
running = True

def draw_map():
    comp_img = generate_terminator_image(day_img, night_img)
    comp_surf = pygame.image.fromstring(comp_img.tobytes(), comp_img.size, comp_img.mode)
    # Fill background black
    screen.fill((0,0,0))
    # Center image
    offset_x = (SCREEN_SIZE[0] - img_w) // 2
    offset_y = (SCREEN_SIZE[1] - img_h) // 2
    screen.blit(comp_surf, (offset_x, offset_y))
    # Overlay city crosses
    overlay_city_markers(screen, img_w, img_h, SCREEN_SIZE[0], SCREEN_SIZE[1])
    pygame.display.flip()

# Initial draw
draw_map()

# --- Main loop ---
clock = pygame.time.Clock()
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_q, pygame.K_ESCAPE):
                running = False
        elif event.type == pygame.USEREVENT:
            draw_map()
    clock.tick(60)

pygame.quit()
# optionally, reboot the system
#os.system("sudo reboot")
sys.exit(0)
