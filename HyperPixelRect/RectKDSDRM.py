#!/usr/bin/env python3
import os
import pygame
import time

# --- SDL2 KMS/DRM environment ---
os.environ["SDL_VIDEODRIVER"] = "KMSDRM"
os.environ["SDL_KMSDRM_DEVICE"] = "/dev/dri/card0"
os.environ["SDL_NOMOUSE"] = "1"

# --- Initialize Pygame ---
pygame.init()
pygame.display.init()
pygame.mouse.set_visible(False)

# --- Screen size for HyperPixel 4.0 Rectangle ---
SCREEN_SIZE = (480, 800)
screen = pygame.display.set_mode(SCREEN_SIZE, pygame.FULLSCREEN)

# --- Fill red ---
screen.fill((255, 0, 0))
pygame.display.flip()

# --- Keep display ---
time.sleep(5)

# --- Clean exit ---
pygame.quit()
