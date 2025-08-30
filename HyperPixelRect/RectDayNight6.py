#!/usr/bin/env python3
# HyperPixel Day/Night Terminator — exits with Q or ESC (and handles SIGTERM)

import os, sys, math, signal, time
from datetime import datetime, timezone
from PIL import Image

# --- Quiet pygame banner & pick GUI driver ---
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
os.environ["SDL_VIDEODRIVER"] = "x11"   # running from a terminal in the GUI
# Optional: disable screensaver if your desktop blanks the display
os.environ.setdefault("SDL_VIDEO_ALLOW_SCREENSAVER", "0")
import pygame

pygame.init()
pygame.mouse.set_visible(False)

# --- Screen / assets ---
screen = pygame.display.set_mode((800, 480), pygame.FULLSCREEN)
SCREEN_SIZE = screen.get_size()

day_img  = Image.open("day.jpg").convert("RGB").resize(SCREEN_SIZE)
night_img= Image.open("night.jpg").convert("RGB").resize(SCREEN_SIZE)

# --- Simple solar model ---
def solar_declination(day_of_year):
    # Approximate declination in radians
    return math.radians(23.44) * math.sin(math.radians(360 * (284 + day_of_year) / 365))

def is_day(lat_deg, lon_deg, utc_datetime):
    lat = math.radians(lat_deg)
    n   = utc_datetime.timetuple().tm_yday
    decl= solar_declination(n)

    frac_hour = utc_datetime.hour + utc_datetime.minute/60 + utc_datetime.second/3600
    subsolar_lon = (frac_hour / 24.0) * 360 - 180  # degrees
    lon = math.radians(lon_deg)

    H = lon - math.radians(subsolar_lon)  # hour angle in radians
    cos_zenith = math.sin(lat)*math.sin(decl) + math.cos(lat)*math.cos(decl)*math.cos(H)
    return cos_zenith > 0

def generate_terminator_surface():
    """Build the day/night composite once and return a pygame Surface."""
    now = datetime.now(timezone.utc)
    w, h = SCREEN_SIZE
    mask = Image.new("1", (w, h))
    # Build mask row-by-row (quick enough at 800x480)
    for y in range(h):
        lat = 90 - (y / h) * 180.0
        for x in range(w):
            lon = (x / w) * 360.0 - 180.0
            mask.putpixel((x, y), 1 if is_day(lat, lon, now) else 0)
    comp = Image.composite(day_img, night_img, mask)
    return pygame.image.fromstring(comp.tobytes(), SCREEN_SIZE, comp.mode)

# --- Exit handling ---
running = True
def handle_sigterm(sig, frame):
    global running
    running = False
signal.signal(signal.SIGTERM, handle_sigterm)

clock = pygame.time.Clock()
next_update = 0.0
current_surface = None

# --- Main loop ---
while running:
    # 1) Events — Q or ESC exits immediately
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_q, pygame.K_ESCAPE):
                running = False

    # 2) Update composite at most once per minute
    now_mono = time.monotonic()
    if (current_surface is None) or (now_mono >= next_update):
        current_surface = generate_terminator_surface()
        next_update = now_mono + 60.0  # refresh period (seconds)

    # 3) Draw
    screen.blit(current_surface, (0, 0))
    pygame.display.flip()

    # 4) Poll ~60 times/sec so keypress is responsive
    clock.tick(60)

pygame.quit()
sys.exit(0)
