import  os
import sys
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
os.environ["SDL_NOMOUSE"] = "1"   # disables mouse subsystem
import pygame

# Initialize Pygame
pygame.init()

# Full-screen mode on your HyperPixel
screen = pygame.display.set_mode((800, 480), pygame.FULLSCREEN)
pygame.display.set_caption("Full-Screen HyperPixel Display")
pygame.mouse.set_visible(False)

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False  # Exit on ESC

    # Example: Fill background black
    screen.fill((0, 0, 0))

    # Draw something (yellow circle in center)
    pygame.draw.circle(screen, (255, 255, 0), (400, 240), 80)

    # Update display
    pygame.display.flip()

pygame.quit()
sys.exit()
