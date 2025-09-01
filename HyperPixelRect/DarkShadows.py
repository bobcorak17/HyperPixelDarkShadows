#!/home/pi/HyperPixel/.venv/bin/python3
# DarkShadows.py

import os
# must set this BEFORE importing pygame
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
os.environ.setdefault("SDL_VIDEO_ALLOW_SCREENSAVER", "0")
os.environ["SDL_VIDEO_WINDOW_POS"] = "0,0"
os.environ["SDL_VIDEO_FOREIGN"] = "1"
import pygame

import sys, math, signal,time
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageFilter, ImageDraw
import threading
import numpy as np
import ephem

# -----------------------
# Configuration
# -----------------------
DAY_IMAGE_PATH   = "day.jpg"    # your 400x800 day image
NIGHT_IMAGE_PATH = "night.jpg"  # your 400x800 night image
TWILIGHT_BLUR_RADIUS = 4        # set 0 to disable
UPDATE_FPS = 10                 # update redraws per second (10 is a good compromise)
NORMAL_OPS = True
ANIMATION = not NORMAL_OPS
ANIMATION_INTERVAL = timedelta(days=1)

CITIES = {
    "Null Island": (0.0, 0.0),
    "Portage": (42.2012, -85.5800),
    "Tokyo": (35.6895, 139.6917),
    "Stockholm": (59.3293, 18.0686),
    "Honolulu": (21.3069, -157.8583),
    "NYC": (40.7128, -74.0060),
    "LA": (34.0522, -118.2437),
    "Tierra del Fuego": (-54.8019, -68.3029),
    "Sydney": (-33.8688, 151.2093),
    "João Pessoa": (-7.115, -34.86306),
    "Cape Town": (-33.917419, 18.386274),
}

# state
running = True
terminator_surface = None
lock = threading.Lock()

#initialize the display
pygame.init()
pygame.mouse.set_visible(False)
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
SCREEN_SIZE = screen.get_size()
screen_w, screen_h = SCREEN_SIZE

clock = pygame.time.Clock()

# -----------------------------
# Load images
# -----------------------------
day_img   = Image.open(DAY_IMAGE_PATH).convert("RGB")
night_img = Image.open(NIGHT_IMAGE_PATH).convert("RGB")
img_w, img_h = day_img.size
offset_x = (screen_w - img_w) // 2
offset_y = (screen_h - img_h) // 2

def subsolar_point(dt_utc):
    """Compute the subsolar point (lat, lon) in degrees at a given UTC datetime using PyEphem."""
    obs = ephem.Observer()
    obs.date = dt_utc
    obs.lon = '0'   # Greenwich
    obs.lat = '0'   # Equator
    sun = ephem.Sun(obs)

    # Latitude of subsolar point is just the Sun's declination
    lat_deg = math.degrees(sun.dec)

    # Subsolar longitude = RA - GMST
    ra_deg = math.degrees(sun.ra)
    gmst_deg = math.degrees(obs.sidereal_time())
    lon_deg = (ra_deg - gmst_deg + 540.0) % 360.0 - 180.0
    return lat_deg, lon_deg

def sublunar_point(dt_utc: datetime):
    """Return (lat_deg, lon_deg) of the sublunar point at UTC datetime dt_utc.
    Uses PyEphem for the Moon's apparent geocentric RA/Dec.
    """
    obs = ephem.Observer()
    obs.date = dt_utc
    obs.lon = '0'   # Greenwich reference
    obs.lat = '0'   # Equator
    moon = ephem.Moon(obs)

    # Latitude of sublunar point is Moon's declination
    lat_deg = math.degrees(moon.dec)

    # Sub-lunar longitude = RA - GMST
    ra_deg = math.degrees(moon.ra)
    gmst_deg = math.degrees(obs.sidereal_time())
    lon_deg = (ra_deg - gmst_deg + 540.0) % 360.0 - 180.0
    return lat_deg, lon_deg

def generate_terminator_pil(day_img: Image.Image,
                            night_img: Image.Image,
                            dt_utc,
                            twilight_blur=TWILIGHT_BLUR_RADIUS):
    """
    Vectorized generation of day/night terminator for 400x800 images.
    Returns a PIL.Image with blended day/night and twilight smoothing.
    """
    ####print("===", datetime.now(timezone.utc))
    w, h = day_img.size

    # Create arrays for lat/lon per pixel
    x = np.linspace(-180, 180, w)
    y = np.linspace(90, -90, h)  # top=+90°, bottom=-90°
    lon_grid, lat_grid = np.meshgrid(x, y)

    # Compute cosine of solar zenith angle using ephem subsolar point
    obs = ephem.Observer()
    obs.date = dt_utc
    sun = ephem.Sun(obs)
    decl_rad = float(sun.dec)
    ra_rad = float(sun.ra)

    # GMST
    jd = ephem.julian_date(dt_utc)
    gmst_deg = (280.46061837 + 360.98564736629 * (jd - 2451545.0)) % 360
    gmst_rad = math.radians(gmst_deg)

    subsolar_lon_rad = ra_rad - gmst_rad

    lat_rad = np.radians(lat_grid)
    lon_rad = np.radians(lon_grid)
    H = lon_rad - subsolar_lon_rad
    cos_zenith = np.sin(lat_rad) * math.sin(decl_rad) + np.cos(lat_rad) * np.cos(decl_rad) * np.cos(H)

    # Map cos_zenith to 0..255 with twilight smoothing
    # Linear ramp from -0.02..+0.02
    mask_array = np.clip((cos_zenith + 0.02) / 0.04, 0.0, 1.0) * 255
    mask_array = mask_array.astype(np.uint8)

    # Apply Gaussian blur for twilight transition
    #mask_img = Image.fromarray(mask_array, mode="L")
    mask_img = Image.fromarray(mask_array.astype("uint8"))
    if twilight_blur > 0:
        mask_img = mask_img.filter(ImageFilter.GaussianBlur(radius=twilight_blur))

    # Blend day/night images
    day_arr = np.array(day_img, dtype=np.uint8)
    night_arr = np.array(night_img, dtype=np.uint8)
    mask_arr = np.array(mask_img, dtype=np.float32) / 255.0  # normalize 0..1

    blended_arr = (day_arr * mask_arr[..., None] + night_arr * (1 - mask_arr[..., None])).astype(np.uint8)
    blended_img = Image.fromarray(blended_arr)
    ###print("---", datetime.now(timezone.utc))
    ###print()
    return blended_img


def pil_to_pygame_surface(pil_img):
    """ Utility: center PIL image on pygame screen
    """
    return pygame.image.fromstring(pil_img.tobytes(), pil_img.size, pil_img.mode)

def draw_markers_on_pil(pil_img, lat, lon, color):
    """ Draw a cross on a PIL image.
    """
    draw = ImageDraw.Draw(pil_img)
    w, h = pil_img.size

    x = int((lon + 180.0) / 360.0 * w)
    y = int((90.0 - lat) / 180.0 * h)
    size = 6
    draw.line((x - size, y, x + size, y), fill=color, width=2)
    draw.line((x, y - size, x, y + size), fill=color, width=2)
    return

def draw_city_crosses_on_pil(pil_img, cities):
    """ Draw a red cross over our landmarks  on a PIL image.
    """
    for name, (lat, lon) in cities.items():
        draw_markers_on_pil(pil_img, lat, lon, color=(255, 0, 0))
    return

def draw_subsolar_point_on_pil(pil_img, dt_utc, color=(255, 255, 0)):
    """ Draw a yellow cross where the sun is directly overhead (subsolar point) on a PIL image.
    """
    lat, lon = subsolar_point(dt_utc)
    draw_markers_on_pil(pil_img, lat, lon, color=(255, 255, 0))
    return

def draw_sublunar_point_on_pil(pil_img, dt_utc, color=(0, 255, 255)):
    """Draw a cyan cross where the moon is directly overhead (sublunar point) on a PIL image.
    """
    lat, lon = sublunar_point(dt_utc)
    draw_markers_on_pil(pil_img, lat, lon, color=(0, 255, 255))
    return

def update_terminator(surface):
    global terminator_surface
    now = None
    last_dt = None

    while running:
        if NORMAL_OPS:
            now = datetime.now(timezone.utc)

        elif ANIMATION:
            if now is None:
                now = datetime.now(timezone.utc)
            else:
                now = now + ANIMATION_INTERVAL

        # Only recompute mask when time has advanced enough for smoothness
        # We'll recompute at UPDATE_FPS; keep CPU reasonable
        if surface is None or last_dt is None or (now - last_dt).total_seconds() >= 1.0/UPDATE_FPS:
            pil_for_map = generate_terminator_pil(day_img, night_img, now, twilight_blur=TWILIGHT_BLUR_RADIUS)
            # draw crosses on a copy so the base day/night remains pristine
            draw_city_crosses_on_pil(pil_for_map, CITIES)
            draw_subsolar_point_on_pil(pil_for_map, now)
            draw_sublunar_point_on_pil(pil_for_map, now)
            surface = pil_to_pygame_surface(pil_for_map)
            last_dt = now

            surf = pygame.image.fromstring(pil_for_map.tobytes(), pil_for_map.size, pil_for_map.mode)

            with lock:
                terminator_surface = surf

            time.sleep(1.0 / UPDATE_FPS)
    return

# -----------------------
# Main program
# -----------------------
def main():
    # handle SIGTERM cleanly
    def _sigterm(sig, frame):
        #nonlocal running
        running = False
    signal.signal(signal.SIGTERM, _sigterm)

    current_surface = None
    global running
    threading.Thread(target=update_terminator, kwargs={"surface": current_surface}, daemon=True).start()

    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False

        if terminator_surface:
            with lock:
                # draw centered with black background
                screen.fill((0,0,0))
                screen.blit(terminator_surface, (offset_x, offset_y))
                pygame.display.flip()

        clock.tick(UPDATE_FPS)

    pygame.quit()
    sys.exit(0)

if __name__ == "__main__":
    main()
