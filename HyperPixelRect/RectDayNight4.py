#!/usr/bin/env python3
import os
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

# --- load day/night images (480x800 or scaled) ---
day_img = Image.open("day.jpg").convert("RGB").resize(SCREEN_SIZE)
night_img = Image.open("night.jpg").convert("RGB").resize(SCREEN_SIZE)

def sun_position_fraction_utc():
    """Return the fraction of the day (0..1) for the subsolar longitude."""
    now = datetime.now(timezone.utc)
    return (now.hour + now.minute/60 + now.second/3600) / 24

def generate_terminator_mask(width, height):
    """
    Generates a binary mask (mode '1') for day/night using a simple subsolar longitude approximation.
    This is not a perfect astronomical model, but gives a reasonable curved terminator.
    """
    mask = Image.new("1", (width, height))

    # current UTC fraction of day
    frac = sun_position_fraction_utc()

    # compute subsolar longitude (-180..180 mapped to image x)
    subsolar_x = int(width * frac)

    for y in range(height):
        lat = (0.5 - y/height) * 180  # latitude in degrees
        for x in range(width):
            lon = (x/width - 0.5) * 360  # longitude in degrees
            # simple cosine illumination model:
            angle = (lon - frac*360) * math.pi / 180
            if math.cos(angle) > 0:
                mask.putpixel((x, y), 1)  # day
            else:
                mask.putpixel((x, y), 0)  # night
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
