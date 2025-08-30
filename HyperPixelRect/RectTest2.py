#!/usr/bin/env python3
import os
import sys
import signal
import time
from PIL import Image
import pygame

# --- Framebuffer environment ---
os.environ["SDL_VIDEODRIVER"] = "fbcon"
os.environ["SDL_FBDEV"] = "/dev/fb0"   # Update to /dev/fb1 if your HyperPixel uses fb1
os.environ["SDL_NOMOUSE"] = "1"        # disable mouse subsystem

# --- Initialize Pygame ---
pygame.init()
pygame.display.init()
pygame.mouse.set_visible(False)  # hide mouse

# --- Screen config ---
SCREEN_SIZE = (720, 720)   # must match framebuffer
screen = pygame.display.set_mode(SCREEN_SIZE, pygame.FULLSCREEN)

# --- Load image ---
IMAGE_PATH = "/home/pi/graphicstest/sonos.png"
if os.path.exists(IMAGE_PATH):
    img = Image.open(IMAGE_PATH).convert("RGB")

    # --- Resize manually to fit screen while keeping aspect ratio ---
    img_width, img_height = img.size
    max_width, max_height = SCREEN_SIZE
    scale = min(max_width / img_width, max_height / img_height)
    new_size = (int(img_width * scale), int(img_height * scale))
    img = img.resize(new_size, Image.ANTIALIAS)
else:
    img = Image.new("RGB", SCREEN_SIZE, "black")

# --- Center image ---
bg = Image.new("RGB", SCREEN_SIZE, "black")
pos = ((SCREEN_SIZE[0] - img.width)//2, (SCREEN_SIZE[1] - img.height)//2)
bg.paste(img, pos)

# --- Convert to pygame surface and display ---
surf = pygame.image.fromstring(bg.tobytes(), bg.size, bg.mode)
screen.blit(surf, (0, 0))
pygame.display.flip()

# --- Handle stop signals ---
def stop(sig, frame):
    screen.fill((0, 0, 0))  # fill black on stop
    pygame.display.flip()
    pygame.quit()
    sys.exit(0)

signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)

# --- Idle loop ---
while True:
    time.sleep(1)
