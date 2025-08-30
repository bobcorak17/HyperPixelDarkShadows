#!/usr/bin/env python3
import os
import pygame
from PIL import Image

# --- hide pygame banner ---
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
os.environ["SDL_VIDEODRIVER"] = "x11"  # GUI terminal

# --- initialize pygame ---
pygame.init()
pygame.mouse.set_visible(False)

# --- open fullscreen surface ---
screen = pygame.display.set_mode((800, 480), pygame.FULLSCREEN)

# --- load JPEG via PIL ---
try:
    img = Image.open("night.jpg")  # replace with your JPEG file
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
