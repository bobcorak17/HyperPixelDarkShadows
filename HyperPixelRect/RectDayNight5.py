#!/usr/bin/env python3

# --- hide pygame banner ---
import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
os.environ["SDL_VIDEODRIVER"] = "x11"

import pygame
from PIL import Image
import math
from datetime import datetime, timezone
import time

# --- environment ---
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
os.environ["SDL_VIDEODRIVER"] = "x11"

pygame.init()
pygame.mouse.set_visible(False)

SCREEN_SIZE = (800, 480)
screen = pygame.display.set_mode(SCREEN_SIZE, pygame.FULLSCREEN)

# --- load day/night images ---
day_img = Image.open("day.jpg").convert("RGB").resize(SCREEN_SIZE)
night_img = Image.open("night.jpg").convert("RGB").resize(SCREEN_SIZE)

def solar_declination(day_of_year):
    """Approximate solar declination in radians."""
    return math.radians(23.44) * math.sin(math.radians(360*(284 + day_of_year)/365))

def is_day(lat_deg, lon_deg, utc_datetime):
    """
    Return True if the sun is above the horizon at given lat/lon and UTC datetime.
    Simple model: computes solar hour angle and compares zenith.
    """
    lat = math.radians(lat_deg)
    day_of_year = utc_datetime.timetuple().tm_yday
    decl = solar_declination(day_of_year)

    # fractional UTC hour
    frac_hour = utc_datetime.hour + utc_datetime.minute/60 + utc_datetime.second/3600

    # subsolar longitude
    subsolar_lon = (frac_hour / 24.0) * 360 - 180
    lon = math.radians(lon_deg)

    # hour angle
    H = lon - math.radians(subsolar_lon)

    # cosine of solar zenith
    cos_zenith = math.sin(lat)*math.sin(decl) + math.cos(lat)*math.cos(decl)*math.cos(H)
    return cos_zenith > 0  # day if sun above horizon

def generate_terminator_mask(width, height):
    mask = Image.new("1", (width, height))
    now = datetime.now(timezone.utc)
    for y in range(height):
        lat = 90 - (y/height)*180  # top=+90°, bottom=-90°
        for x in range(width):
            lon = (x/width)*360 - 180  # left=-180°, right=+180°
            if is_day(lat, lon, now):
                mask.putpixel((x, y), 1)
            else:
                mask.putpixel((x, y), 0)
    return mask

try:
    while True:
        mask = generate_terminator_mask(*SCREEN_SIZE)
        terminator_img = Image.composite(day_img, night_img, mask)
        surf = pygame.image.fromstring(terminator_img.tobytes(), SCREEN_SIZE, terminator_img.mode)
        screen.blit(surf, (0, 0))
        pygame.display.flip()
        time.sleep(60)  # update every minute
except KeyboardInterrupt:
    pygame.quit()

