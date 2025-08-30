#!/usr/bin/env python3
# DarkShadows: HyperPixel Day/Night Terminator Display
# Exits on Q or ESC, handles SIGTERM, smooth twilight, city markers

import os, sys, math, signal, time
from datetime import datetime, timezone
from PIL import Image, ImageFilter

# --- Set environment BEFORE importing pygame ---
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
os.environ["SDL_VIDEODRIVER"] = "x11"  # run in GUI terminal
os.environ.setdefault("SDL_VIDEO_ALLOW_SCREENSAVER", "0")
os.environ["SDL_VIDEO_WINDOW_POS"] = "0,0"
os.environ["SDL_VIDEO_FOREIGN"] = "1"

import pygame

# --- Configuration ---
DAY_IMAGE_PATH = "day.jpg"  # 400x800
NIGHT_IMAGE_PATH = "night.jpg"  # 400x800

CITIES = {
    "Null Island": (0.0, 0.0),
    "Tokyo":(35.6895, 139.6917),
    "Stockholm":(59.3293, 18.0686),
    "Honolulu":(21.3069, -157.8583),
    "NYC":(40.7128, -74.0060),
    "LA":(34.0522, -118.2437),
    "Tierra del Fuego":(-54.8019, -68.3029),
    "Sydney":(-33.8688, 151.2093),
}

TWILIGHT_WIDTH = 5  # pixels for smooth transition

# --- Screen setup ---
pygame.init()
pygame.mouse.set_visible(False)
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
SCREEN_W, SCREEN_H = screen.get_size()

# --- Load images ---
day_img = Image.open(DAY_IMAGE_PATH).convert("RGB")
night_img = Image.open(NIGHT_IMAGE_PATH).convert("RGB")


# --- Solar functions ---
def solar_declination(day_of_year):
    return math.radians(23.44) * math.sin(math.radians(360 * (284 + day_of_year) / 365))


def is_day(lat_deg, lon_deg, now):
    lat = math.radians(lat_deg)
    n = now.timetuple().tm_yday
    decl = solar_declination(n)
    frac_hour = now.hour + now.minute / 60 + now.second / 3600
    subsolar_lon = -(frac_hour / 24.0) * 360 - 180
    lon = math.radians(lon_deg)
    H = lon - math.radians(subsolar_lon)
    cos_zenith = math.sin(lat) * math.sin(decl) + math.cos(lat) * math.cos(decl) * math.cos(H)
    return cos_zenith


def generate_terminator_surface():
    now = datetime.now(timezone.utc)
    w, h = day_img.size
    mask = Image.new("L", (w, h))  # 8-bit grayscale for twilight

    for y in range(h):
        lat = 90 - (y / h) * 180.0
        for x in range(w):
            lon = (x / w) * 360.0 - 180.0
            cos_zen = is_day(lat, lon, now)
            if cos_zen >= 0.01:
                val = 255
            elif cos_zen <= -0.01:
                val = 0
            else:
                # Linear interpolation for twilight
                val = int((cos_zen + 0.01) / 0.02 * 255)
            mask.putpixel((x, y), val)

    mask = mask.filter(ImageFilter.GaussianBlur(radius=TWILIGHT_WIDTH))
    comp = Image.composite(day_img, night_img, mask)
    return comp


# --- City markers ---
def latlon_to_xy(lat, lon, w, h):
    x = int((lon + 180.0) / 360.0 * w)
    y = int((90.0 - lat) / 180.0 * h)
    return x, y


def draw_cross(surface, x, y, color=(255, 0, 0), size=5):
    pygame.draw.line(surface, color, (x - size, y), (x + size, y), 2)
    pygame.draw.line(surface, color, (x, y - size), (x, y + size), 2)


def overlay_city_markers(surface, w, h):
    for latlon in CITIES.values():
        x, y = latlon_to_xy(latlon[0], latlon[1], w, h)
        draw_cross(surface, x, y)


# --- Exit handling ---
running = True


def handle_sigterm(sig, frame):
    global running
    running = False

signal.signal(signal.SIGTERM, handle_sigterm)

clock = pygame.time.Clock()
last_comp = None

# --- Main loop ---
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_q, pygame.K_ESCAPE):
                running = False

    # Generate composite
    comp = generate_terminator_surface()
    # Resize to fit screen, maintain 400x800 aspect, centered
    comp_w, comp_h = comp.size
    scale = min(SCREEN_W / comp_w, SCREEN_H / comp_h)
    new_w, new_h = int(comp_w * scale), int(comp_h * scale)
    comp_resized = comp.resize((new_w, new_h), Image.LANCZOS)
    comp_surface = pygame.image.fromstring(comp_resized.tobytes(), (new_w, new_h), comp_resized.mode)

    # Center on screen
    x_off = (SCREEN_W - new_w) // 2
    y_off = (SCREEN_H - new_h) // 2

    overlay_city_markers(comp_surface, new_w, new_h)

    screen.fill((0, 0, 0))
    screen.blit(comp_surface, (x_off, y_off))
    pygame.display.flip()

    clock.tick(60)  # smooth updates and responsive keys

pygame.quit()
sys.exit(0)
