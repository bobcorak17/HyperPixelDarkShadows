#!/usr/bin/env python3
import os
import pygame
from PIL import Image
import math
from datetime import datetime, timezone

# --- environment ---
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
os.environ["SDL_VIDEODRIVER"] = "x11"

pygame.init()
pygame.mouse.set_visible(False)

SCREEN_SIZE = (800, 480)
screen = pygame.display.set_mode(SCREEN_SIZE, pygame.FULLSCREEN)

# --- load images ---
day_img = Image.open("day.jpg").convert("RGB").resize(SCREEN_SIZE)
night_img = Image.open("night.jpg").convert("RGB").resize(SCREEN_SIZE)

# --- simple solar terminator approximation ---
def generate_mask(width, height):
    mask = Image.new("1", (width, height))
    
    # current UTC time as fraction of day (0..1)
    now = datetime.now(timezone.utc)
    day_fraction = (now.hour + now.minute/60 + now.second/3600)/24
    
    # compute longitude of subsolar point (simplified)
    # 0..1 mapped to left->right of image
    subsolar_x = int(day_fraction * width)
    
    for y in range(height):
        for x in range(width):
            # pixels to the left of subsolar_x are "day"
            if x <= subsolar_x:
                mask.putpixel((x, y), 1)
            else:
                mask.putpixel((x, y), 0)
    return mask

mask = generate_mask(*SCREEN_SIZE)

# --- composite day/night using mask ---
terminator_img = Image.composite(day_img, night_img, mask)

# --- convert to pygame surface and display ---
surf = pygame.image.fromstring(terminator_img.tobytes(), SCREEN_SIZE, terminator_img.mode)
screen.blit(surf, (0, 0))
pygame.display.flip()

# --- keep display ---
pygame.time.wait(5000)
pygame.quit()
