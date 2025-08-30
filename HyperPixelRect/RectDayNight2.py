#!/usr/bin/env python3
import os
import pygame
from PIL import Image

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
os.environ["SDL_VIDEODRIVER"] = "x11"

pygame.init()
pygame.mouse.set_visible(False)

SCREEN_SIZE = (800, 480)
screen = pygame.display.set_mode(SCREEN_SIZE, pygame.FULLSCREEN)

# Load day/night images
day_img = Image.open("day.jpg").convert("RGB").resize(SCREEN_SIZE)
night_img = Image.open("night.jpg").convert("RGB").resize(SCREEN_SIZE)

# --- Create a mask: True = day, False = night ---
mask = Image.new("1", SCREEN_SIZE)
for y in range(SCREEN_SIZE[1]):
    for x in range(SCREEN_SIZE[0]):
        if y > SCREEN_SIZE[1] - (SCREEN_SIZE[1]/SCREEN_SIZE[0])*x:  # placeholder diagonal
            mask.putpixel((x, y), 1)  # day
        else:
            mask.putpixel((x, y), 0)  # night

# --- Combine day/night using mask ---
terminator_img = Image.composite(day_img, night_img, mask)

# Convert to Pygame surface and display
surf = pygame.image.fromstring(terminator_img.tobytes(), SCREEN_SIZE, terminator_img.mode)
screen.blit(surf, (0, 0))
pygame.display.flip()

# Keep display for testing
pygame.time.wait(5000)
pygame.quit()
