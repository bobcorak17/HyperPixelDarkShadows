import os,io
import requests
import queue
from PIL import Image
from soco.discovery import by_name
from soco.events import event_listener

# must set this BEFORE importing pygame
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
os.environ.setdefault("SDL_VIDEO_ALLOW_SCREENSAVER", "0")
os.environ["SDL_VIDEO_WINDOW_POS"] = "0,0"
os.environ["SDL_VIDEO_FOREIGN"] = "1"
import pygame

# -------------------
# Setup Sonos
# -------------------
ZONE_NAME = "Basement"

# Connect to the Sonos player by name
zone = by_name(ZONE_NAME)
if zone is None:
    raise RuntimeError(f"Sonos zone '{ZONE_NAME}' not found")

# Subscribe to AVTransport events
sub = zone.avTransport.subscribe(auto_renew=True)

# -------------------
# Setup Pygame
# -------------------
pygame.init()
pygame.display.set_caption("Sonos Album Art")
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.mouse.set_visible(False)
clock = pygame.time.Clock()

running = True
need_redraw = True  # only flip screen when necessary

# -------------------
# Helpers
# -------------------
def get_album_art_image(uri):
    """Fetch Sonos album art and return as a Pygame Surface."""
    if not uri:
        return None
    if uri.startswith("http"):
        url = uri
    else:
        url = f"http://{zone.ip_address}:1400{uri}"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        image = Image.open(io.BytesIO(response.content))
        # Scale to screen
        image = image.resize(screen.get_size(), Image.LANCZOS)
        return pygame.image.fromstring(image.tobytes(), image.size, image.mode).convert()
    except Exception as e:
        print(f"Error fetching album art: {e}")
        return None

# -------------------
# Main loop
# -------------------
while running:
    # Handle Sonos events
    try:
        sonos_event = sub.events.get(timeout=0.5)
        if sonos_event is not None:
            state = sonos_event.variables.get("transport_state")

            if state in ("PLAYING", "TRANSITIONING"):
                track = zone.get_current_track_info()
                image = get_album_art_image(track["album_art"])
                if image:
                    screen.blit(image, (0, 0))
                need_redraw = True
            else:
                # Not playing → blank screen
                screen.fill((0, 0, 0))
                need_redraw = True
    except queue.Empty:
        pass

    # Handle quit keys/events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.unicode.lower() == 'q':
                running = False

    # Only redraw when needed
    if need_redraw:
        pygame.display.flip()
        need_redraw = False

    # Keep loop light
    clock.tick(10)

# -------------------
# Cleanup
# -------------------
sub.unsubscribe()
event_listener.stop()
pygame.quit()
