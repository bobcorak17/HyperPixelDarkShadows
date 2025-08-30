#!/usr/bin/env python3
# --- hide pygame banner ---
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
os.environ["SDL_VIDEODRIVER"] = "x11"

import os
import pygame
from PIL import Image

# --- initialize pygame ---
pygame.init()
pygame.mouse.set_visible(False)

SCREEN_SIZE = (800, 480)
screen = pygame.display.set_mode(SCREEN_SIZE, pygame.FULLSCREEN)

# --- load images ---
day_img = Image.open("day.jpg").convert("RGB").resize(SCREEN_SIZE)
night_img = Image.open("night.jpg").convert("RGB").resize(SCREEN_SIZE)

# --- create pygame surfaces ---
day_surf = pygame.image.fromstring(day_img.tobytes(), SCREEN_SIZE, day_img.mode)
night_surf = pygame.image.fromstring(night_img.tobytes(), SCREEN_SIZE, night_img.mode)

# --- draw diagonal blend ---
for y in range(SCREEN_SIZE[1]):
    for x in range(SCREEN_SIZE[0]):
        if y > SCREEN_SIZE[1] - (SCREEN_SIZE[1]/SCREEN_SIZE[0])*x:  # below diagonal
            screen.set_at((x, y), day_surf.get_at((x, y)))
        else:  # above diagonal
            screen.set_at((x, y), night_surf.get_at((x, y)))

pygame.display.flip()

# --- keep display ---
pygame.time.wait(5000)
pygame.quit()
