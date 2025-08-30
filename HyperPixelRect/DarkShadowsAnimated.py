#!/usr/bin/env python3
# DarkShadows — HyperPixel Day/Night Terminator Display

import os, sys, math, signal, time
from datetime import datetime, timezone
from PIL import Image

# --- Quiet pygame banner & environment MUST be before pygame import ---
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
os.environ["SDL_VIDEODRIVER"] = "x11"  # run in GUI mode
os.environ.setdefault("SDL_VIDEO_ALLOW_SCREENSAVER", "0")
os.environ["SDL_VIDEO_WINDOW_POS"] = "0,0"

import pygame  # now banner is suppressed

# -----------------------------
# Configuration
# -----------------------------
DAY_IMAGE_PATH = "day.jpg"      # 400x800
NIGHT_IMAGE_PATH = "night.jpg"  # 400x800

UPDATE_INTERVAL_SEC = 1/30  # ~30 FPS for smooth painting

CITIES = {
    "Null Island": (0.0, 0.0),
    "Tokyo": (35.6895, 139.6917),
    "Stockholm": (59.3293, 18.0686),
    "Honolulu": (21.3069, -157.8583),
    "NYC": (40.7128, -74.0060),
    "LA": (34.0522, -118.2437),
    "Tierra del Fuego": (-54.8019, -68.3029),
    "Sydney":(-33.8688, 151.2093),
}

# -----------------------------
# Solar calculations
# -----------------------------
def solar_declination(day_of_year):
    return math.radians(23.44) * math.sin(math.radians(360*(284 + day_of_year)/365))

def is_day(lat_deg, lon_deg, utc_datetime):
    lat = math.radians(lat_deg)
    day_of_year = utc_datetime.timetuple().tm_yday
    decl = solar_declination(day_of_year)
    frac_hour = utc_datetime.hour + utc_datetime.minute/60 + utc_datetime.second/3600
    subsolar_lon = -(frac_hour / 24.0)*360 - 180
    lon = math.radians(lon_deg)
    H = lon - math.radians(subsolar_lon)
    cos_zenith = math.sin(lat)*math.sin(decl) + math.cos(lat)*math.cos(decl)*math.cos(H)
    return cos_zenith > 0

# -----------------------------
# Image helpers
# -----------------------------
def generate_terminator_surface():
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

def latlon_to_xy(lat, lon, w, h):
    x = int((lon + 180.0)/360.0 * w)
    y = int((90.0 - lat)/180.0 * h)
    return x, y

def draw_cross(surface, x, y, color=(255,0,0), size=5):
    pygame.draw.line(surface, color, (x-size,y), (x+size,y), 2)
    pygame.draw.line(surface, color, (x,y-size), (x,y+size), 2)

def overlay_city_markers(surface, w, h):
    for name, (lat, lon) in CITIES.items():
        x, y = latlon_to_xy(lat, lon, w, h)
        draw_cross(surface, x, y)

# -----------------------------
# Safe exit handling
# -----------------------------
running = True
def handle_sigterm(sig, frame):
    global running
    running = False
signal.signal(signal.SIGTERM, handle_sigterm)

# -----------------------------
# Pygame init
# -----------------------------
pygame.init()
pygame.mouse.set_visible(False)
screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
SCREEN_W, SCREEN_H = screen.get_size()

# Load source images
day_img   = Image.open(DAY_IMAGE_PATH).convert("RGB")
night_img = Image.open(NIGHT_IMAGE_PATH).convert("RGB")
IMG_W, IMG_H = day_img.size

# Calculate offsets to center the 400x800 image
OFFSET_X = (SCREEN_W - IMG_W)//2
OFFSET_Y = (SCREEN_H - IMG_H)//2

# -----------------------------
# Main loop
# -----------------------------
clock = pygame.time.Clock()

while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_q, pygame.K_ESCAPE):
                running = False

    # Generate day/night image
    comp = generate_terminator_surface()
    surf = pygame.image.fromstring(comp.tobytes(), comp.size, comp.mode)
    overlay_city_markers(surf, IMG_W, IMG_H)

    # Clear screen, blit centered
    screen.fill((0,0,0))
    screen.blit(surf, (OFFSET_X, OFFSET_Y))
    pygame.display.flip()

    clock.tick(30)  # smooth updates ~30 FPS

pygame.quit()
sys.exit(0)
