#!/usr/bin/env python3
import os
import time
import pygame

# --- hide pygame banner ---
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

# --- try X11 driver (works from terminal in GUI) ---
os.environ["SDL_VIDEODRIVER"] = "x11"

SCREEN_SIZE = (800, 480)
screen = pygame.display.set_mode(SCREEN_SIZE, pygame.FULLSCREEN)

def main():
    pygame.init()

    # open fullscreen window
    screen = pygame.display.set_mode(SCREEN_SIZE, pygame.FULLSCREEN)

    # hide mouse after screen exists
    pygame.mouse.set_visible(False)

    # fill red
    screen.fill((255, 0, 0))
    pygame.display.flip()

    time.sleep(5)
    pygame.quit()

if __name__ == "__main__":
    main()
