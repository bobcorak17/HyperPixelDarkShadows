import soco
from soco.discovery import by_name
from soco.events import event_listener
from queue import Empty
import requests
from PIL import Image
from io import BytesIO
import pygame

# --- setup Pygame fullscreen ---
pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("Sonos Album Art")
pygame.mouse.set_visible(False)
clock = pygame.time.Clock()

BLACK = (0, 0, 0)

def fetch_album_art(zone):
    """Fetch current album art as a pygame Surface."""
    info = zone.get_current_track_info()
    art_uri = info.get("album_art")

    if not art_uri:
        return None

    if art_uri.startswith("/"):
        art_uri = f"http://{zone.ip_address}:1400{art_uri}"

    resp = requests.get(art_uri, timeout=5)
    resp.raise_for_status()

    img = Image.open(BytesIO(resp.content)).convert("RGB")
    img = img.resize(screen.get_size(), Image.LANCZOS)
    mode, size, data = img.mode, img.size, img.tobytes()
    return pygame.image.fromstring(data, size, mode)

def show_album_art(surface):
    if surface:
        screen.blit(surface, (0, 0))
    else:
        screen.fill(BLACK)
    pygame.display.flip()

# --- connect to Sonos ---
zone = by_name("Basement")
if not zone:
    raise RuntimeError("Basement not found")

sub = zone.avTransport.subscribe(auto_renew=True)

# Initialize with current state
state = zone.get_current_transport_info()["current_transport_state"]
current_surface = fetch_album_art(zone) if state == "PLAYING" else None
show_album_art(current_surface)

running = True
try:
    while running:
        # Handle quit events
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
            ):
                running = False

        # Handle Sonos events
        try:
            sonos_event = sub.events.get(timeout=0.1)
            vars = sonos_event.variables

            # Transport state change → PLAYING, PAUSED_PLAYBACK, STOPPED, etc.
            if "transport_state" in vars:
                state = vars["transport_state"]
                if state == "PLAYING":
                    new_surface = fetch_album_art(zone)
                    if new_surface:
                        current_surface = new_surface
                else:
                    current_surface = None
                show_album_art(current_surface)

            # Track metadata change (new song, new art)
            elif "current_track_meta_data" in vars and state == "PLAYING":
                new_surface = fetch_album_art(zone)
                if new_surface:
                    current_surface = new_surface
                    show_album_art(current_surface)

        except Empty:
            pass

        clock.tick(30)

finally:
    sub.unsubscribe()
    event_listener.stop()
    pygame.quit()
