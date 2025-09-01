from soco.discovery import by_name
import requests
from PIL import Image
from io import BytesIO
import os, time

# --- hide pygame banner ---
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
os.environ["SDL_VIDEODRIVER"] = "x11"  # GUI terminal
import pygame

running = True

# --- initialize pygame ---
pygame.init()
pygame.mouse.set_visible(False)

# --- open fullscreen surface ---
screen = pygame.display.set_mode((800, 480), pygame.FULLSCREEN)

# Get the speaker object by zone name
zoneName= "Basement"
zone = by_name(zoneName)
if zone is None:
    raise RuntimeError(f"Sonos '{zoneName}' zone not found")

while running:
    #pygame.time.wait(500)  # .5 seconds

    info = zone.get_current_transport_info()
    state = info['current_transport_state']

    if state == 'PLAYING':
        # Get track info
        track_info = zone.get_current_track_info()
        album_art_uri = track_info.get("album_art")

        if album_art_uri:
            try:
                # If Sonos returns a relative path, prepend the speaker’s base URL
                if album_art_uri.startswith("/"):
                    base_url = f"http://{zone.ip_address}:1400"
                    album_art_url = base_url + album_art_uri
                else:
                    album_art_url = album_art_uri

                # Fetch and load into PIL
                response = requests.get(album_art_url)
                response.raise_for_status()

                # --- load Image via PIL ---
                img = Image.open(BytesIO(response.content))
                img = img.convert("RGB")
                img = img.resize(screen.get_size())  # scale to fit screen
                data = img.tobytes()
                surf = pygame.image.fromstring(data, img.size, img.mode)
                screen.blit(surf, (0,0))

            except Exception as e:
                # # fallback: show sonos logo if image fails
                # img = Image.open("sonos.png")
                # img = img.convert("RGB")
                # img = img.resize(screen.get_size())  # scale to fit screen
                # data = img.tobytes()
                # surf = pygame.image.fromstring(data, img.size, img.mode)
                # screen.blit(surf, (0, 0))

                # log this error the try again
                # if error count gets too high, show the sonos screen, so figure out how to do that
                pass
        elif state == 'STOPPED' or state == 'PAUSED':
            # # fallback: show sonos logo if image fails
            img = Image.open("sonos.png")
            img = img.convert("RGB")
            img = img.resize(screen.get_size())  # scale to fit screen
            data = img.tobytes()
            surf = pygame.image.fromstring(data, img.size, img.mode)
            screen.blit(surf, (0, 0))

        # --- update display ---
        pygame.display.flip()

    else:
        # not playing; show a black screen
        screen.fill((0, 0, 0))
        pygame.display.flip()

pygame.quit()

