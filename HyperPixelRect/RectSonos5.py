import pygame
import requests
import io
import signal
import sys
from PIL import Image
from soco.discovery import by_name
from soco.events import event_listener
import queue

# -------------------
# Setup Sonos
# -------------------
ZONE_NAME = "Basement"

zone = by_name(ZONE_NAME)
if zone is None:
    raise RuntimeError(f"Sonos zone '{ZONE_NAME}' not found")

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
need_redraw = True

# -------------------
# Graceful Exit Handler
# -------------------
def cleanup_and_exit(*args):
    global running
    running = False
    try:
        sub.unsubscribe()
    except Exception:
        pass
    try:
        event_listener.stop()
    except Exception:
        pass
    pygame.quit()
    sys.exit(0)

# Catch Ctrl-C
signal.signal(signal.SIGINT, cleanup_and_exit)

# -------------------
# Helpers
# -------------------
def get_album_art_image(uri):
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
        image = image.resize(screen.get_size(), Image.LANCZOS)
        return pygame.image.fromstring(image.tobytes(), image.size, image.mode).convert()
    except Exception as e:
        print(f"Error fetching album art: {e}")
        return None

# -------------------
# Main loop
# -------------------
while running:
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
                screen.fill((0, 0, 0))
                need_redraw = True
    except queue.Empty:
        pass

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            cleanup_and_exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.unicode.lower() == 'q':
                cleanup_and_exit()

    if need_redraw:
        pygame.display.flip()
        need_redraw = False

    clock.tick(10)
