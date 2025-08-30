#!/usr/bin/env python3
# DarkShadows.py — accurate sun position, correct eastward motion of terminator

import os
# must set this BEFORE importing pygame
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
os.environ.setdefault("SDL_VIDEO_ALLOW_SCREENSAVER", "0")
os.environ["SDL_VIDEO_WINDOW_POS"] = "0,0"
os.environ["SDL_VIDEO_FOREIGN"] = "1"
import pygame

import sys, math, signal
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageFilter, ImageDraw
import ephem

# -----------------------
# Configuration
# -----------------------
DAY_IMAGE_PATH   = "day.jpg"    # your 400x800 day image
NIGHT_IMAGE_PATH = "night.jpg"  # your 400x800 night image
TWILIGHT_BLUR_RADIUS = 4       # set 0 to disable
UPDATE_FPS = 10                # update redraws per second (10 is a good compromise)

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

# -----------------------
# Astronomical helpers (Meeus-style approximate)
# -----------------------
def datetime_to_julian_day(dt: datetime) -> float:
    """Convert timezone-aware UTC datetime to Julian Day (floating)."""
    # algorithm: convert to UTC JD with epoch 2000-01-01 12:00 = 2451545.0
    # Use POSIX seconds relative to J2000 for robustness:
    # JD = 2451545.0 + (dt_utc - 2000-01-01T12:00Z).total_seconds()/86400
    j2000 = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    delta_seconds = (dt - j2000).total_seconds()
    return 2451545.0 + delta_seconds / 86400.0

def sun_ecliptic_longitude_and_declination(dt: datetime):
    """
    Approximate Sun ecliptic longitude (lambda) and declination (delta) in radians.
    Uses a simple low-cost formula adequate for visualization (Meeus/NOAA style).
    Returns (lambda_rad, decl_rad).
    """
    JD = datetime_to_julian_day(dt)
    n = JD - 2451545.0  # days since J2000.0

    # mean longitude of the Sun (deg) and mean anomaly (deg)
    L = (280.46061837 + 0.98564736629 * n) % 360.0
    g = (357.52772333 + 0.9856002831 * n) % 360.0

    # convert to radians
    Lr = math.radians(L)
    gr = math.radians(g)

    # ecliptic longitude lambda (approx)
    lambda_deg = L + 1.914602 - 0.004817 * math.cos(gr) + 0.000014 * math.sin(2*gr)
    # better expression using periodic terms:
    lambda_deg = L + 1.915 * math.sin(gr) + 0.020 * math.sin(2*gr)
    lambdar = math.radians(lambda_deg % 360.0)

    # obliquity of the ecliptic (approx, degrees -> radians)
    eps_deg = 23.439291 - 0.0000004 * n
    epsr = math.radians(eps_deg)

    # declination δ = arcsin( sin(eps) * sin(lambda) )
    decl = math.asin(math.sin(epsr) * math.sin(lambdar))

    return lambdar, decl

def sun_ra_in_degrees(lambda_rad, epsr):
    """
    Compute Sun's right ascension (RA) in degrees from ecliptic longitude lambda_rad and obliquity epsr.
    RA = atan2(cos(eps)*sin(lambda), cos(lambda))
    """
    x = math.cos(epsr) * math.sin(lambda_rad)
    y = math.cos(lambda_rad)
    ra = math.degrees(math.atan2(x, y))  # atan2(sinλ cosε, cosλ)
    ra = ra % 360.0
    return ra

def greenwich_mean_sidereal_time_degrees(JD):
    """
    GMST in degrees for Julian Day JD.
    Uses standard formula (approx).
    """
    # from Meeus: GMST = 280.46061837 + 360.98564736629*(JD - 2451545) + 0.000387933*T^2 - T^3/38710000
    T = (JD - 2451545.0) / 36525.0
    gmst = 280.46061837 + 360.98564736629 * (JD - 2451545.0) + 0.000387933 * T*T - (T**3) / 38710000.0
    return gmst % 360.0

def subsolar_point(dt_utc):
    """
    Compute the subsolar point (lat, lon) in degrees at a given UTC datetime.
    """
    # Julian Day
    jd = (dt_utc - datetime(2000, 1, 1, 12, tzinfo=timezone.utc)).total_seconds() / 86400.0 + 2451545.0
    n = jd - 2451545.0

    # Mean longitude of the Sun (deg)
    L = (280.460 + 0.9856474 * n) % 360.0
    # Mean anomaly (rad)
    g = math.radians((357.528 + 0.9856003 * n) % 360.0)
    # # Ecliptic longitude (rad)
    # lambda_sun = math.radians(L + 1.915 * math.sin(g) + 0.020 * math.sin(2*g))
    #
    # # Obliquity of the ecliptic (rad)
    # epsilon = math.radians(23.439 - 0.0000004 * n)
    #
    # # Declination of the Sun (lat of subsolar point, deg)
    # decl_rad = math.asin(math.sin(epsilon) * math.sin(lambda_sun))
    # lat_deg = math.degrees(decl_rad)
    #
    # # Right Ascension
    # ra = math.atan2(math.cos(epsilon) * math.sin(lambda_sun), math.cos(lambda_sun))
    # ra_deg = math.degrees(ra) % 360.0
    #
    # # Greenwich Mean Sidereal Time
    # GMST = (280.46061837 + 360.98564736629 * n) % 360.0
    #
    # # Subsolar longitude = RA - GMST
    # lon_deg = (ra_deg - GMST + 540.0) % 360.0 - 180.0
    #
    # return lat_deg, lon_deg
    obs = ephem.Observer()
    obs.date = dt_utc
    sun = ephem.Sun(obs)

    # Latitude of subsolar point is Sun's declination
    lat_deg = math.degrees(sun.dec)

    # Compute subsolar longitude: RA - GMST
    ra_deg = math.degrees(sun.ra)
    jd = ephem.julian_date(dt_utc)
    GMST = (280.46061837 + 360.98564736629 * (jd - 2451545.0)) % 360
    lon_deg = (ra_deg - GMST + 540.0) % 360 - 180.0  # normalize to [-180, 180]

    return lat_deg, lon_deg

def sublunar_point(dt_utc: datetime):
    """
    Return (lat_deg, lon_deg) of the sublunar point at UTC datetime dt_utc.
    Uses PyEphem for the Moon's apparent geocentric RA/Dec.
    """
    jd = datetime_to_julian_day(dt_utc)
    gmst = greenwich_mean_sidereal_time_degrees(jd)

    moon = ephem.Moon()
    moon.compute(dt_utc)              # geocentric apparent RA/Dec at dt_utc
    ra_deg  = math.degrees(float(moon.ra))   # RA in degrees
    dec_deg = math.degrees(float(moon.dec))  # Dec in degrees

    # Sub-Earth longitude of the Moon (normalize to (-180,180])
    lon = (ra_deg - gmst + 540.0) % 360.0 - 180.0
    lat = dec_deg

    return lat, lon
# -----------------------
# Day/night mask builder (uses accurate subsolar point)
# -----------------------
def generate_terminator_pil(day_img: Image.Image, night_img: Image.Image, dt_utc: datetime, twilight_blur=TWILIGHT_BLUR_RADIUS):
    """
    Build a PIL.Image composite (RGB) for the given UTC datetime using accurate sun position.
    day_img and night_img must be the same size (400x800).
    """
    w, h = day_img.size
    #subsolar_lon_deg, decl_rad = compute_subsolar_lon_and_decl(dt_utc) #todo:remove
    #subsolar_lon_rad = math.radians(subsolar_lon_deg)                  #todo:remove
    lat_deg, lon_deg = subsolar_point(dt_utc)

    # Convert for math
    decl_rad = math.radians(lat_deg)
    subsolar_lon_rad = math.radians(lon_deg)

    # create 'L' mask (0..255) using cos zenith
    mask = Image.new("L", (w, h))
    putpixel = mask.putpixel
    for y in range(h):
        lat_deg = 90.0 - (y / h) * 180.0
        lat_rad = math.radians(lat_deg)
        cos_lat = math.cos(lat_rad)
        sin_lat = math.sin(lat_rad)
        for x in range(w):
            lon_deg = (x / w) * 360.0 - 180.0
            lon_rad = math.radians(lon_deg)
            H = lon_rad - subsolar_lon_rad
            cos_zenith = sin_lat * math.sin(decl_rad) + cos_lat * math.cos(decl_rad) * math.cos(H)
            # map cos_zenith to 0..255 with twilight smoothing around 0
            # simple linear mapping with clamping:
            if cos_zenith >= 0.02:
                val = 255
            elif cos_zenith <= -0.02:
                val = 0
            else:
                # around horizon -0.02..+0.02 -> 0..255
                val = int((cos_zenith + 0.02) / (0.04) * 255)
            putpixel((x, y), val)

    if twilight_blur and twilight_blur > 0:
        mask = mask.filter(ImageFilter.GaussianBlur(radius=twilight_blur))

    comp = Image.composite(day_img, night_img, mask)
    return comp

# -----------------------
# Utility: center PIL image on pygame screen
# -----------------------
def pil_to_pygame_surface(pil_img):
    return pygame.image.fromstring(pil_img.tobytes(), pil_img.size, pil_img.mode)

def draw_cross_on_pil(pil_img, lat, lon, color):
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
    """ Draw a red cross over the landmarks in our list on a PIL image.
    """
    for name, (lat, lon) in cities.items():
        draw_cross_on_pil(pil_img, lat, lon, color=(255, 0, 0))
    return

def draw_subsolar_point_on_pil(pil_img, dt_utc, color=(255, 255, 0)):
    """ Draw a yellow cross where the sun is directly overhead (subsolar point) on a PIL image.
    """
    lat, lon = subsolar_point(dt_utc)
    draw_cross_on_pil(pil_img, lat, lon, color=(255, 255, 0))
    return

def draw_sublunar_point_on_pil(pil_img, dt_utc, color=(0, 255, 255)):
    """Draw a cyan cross where the moon is directly overhead (sublunar point) on a PIL image.
    """
    lat, lon = sublunar_point(dt_utc)
    draw_cross_on_pil(pil_img, lat, lon, color=(0, 255, 255))
    return
# -----------------------
# Main program
# -----------------------
def main():
    # initialize pygame (after env var set)
    pygame.init()
    pygame.mouse.set_visible(False)
    screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
    screen_w, screen_h = screen.get_size()

    # load 400x800 images (do not stretch)
    day_img = Image.open(DAY_IMAGE_PATH).convert("RGB")
    night_img = Image.open(NIGHT_IMAGE_PATH).convert("RGB")
    if day_img.size != night_img.size:
        print("day/night images must be same size", file=sys.stderr)
        return

    img_w, img_h = day_img.size
    offset_x = (screen_w - img_w)//2
    offset_y = (screen_h - img_h)//2

    # state
    running = True
    time_offset_hours = 0  # toggled by T
    clock = pygame.time.Clock()

    # handle SIGTERM cleanly
    def _sigterm(sig, frame):
        nonlocal running
        running = False
    signal.signal(signal.SIGTERM, _sigterm)

    last_dt = None
    current_surface = None

    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif ev.key == pygame.K_r:
                    pygame.quit()
                    os.system("sudo reboot now")
                elif ev.key == pygame.K_t:
                    time_offset_hours = 12 if time_offset_hours == 0 else 0
                    current_surface = None  # force redraw

        now = datetime.now(timezone.utc) + timedelta(hours=time_offset_hours)
        '''# Hard-code local time (e.g. 2025-08-29 20:00 local)
        local_time = datetime(2025, 8, 29, 21, 0)
        # Convert to UTC
        now = local_time.astimezone(timezone.utc)'''

        # Only recompute mask when time has advanced enough for smoothness
        # We'll recompute at UPDATE_FPS; keep CPU reasonable
        if current_surface is None or last_dt is None or (now - last_dt).total_seconds() >= 1.0/UPDATE_FPS:
            pil_comp = generate_terminator_pil(day_img, night_img, now, twilight_blur=TWILIGHT_BLUR_RADIUS)
            # draw crosses on a copy so the base day/night remains pristine
            pil_with_crosses = pil_comp.copy()
            draw_city_crosses_on_pil(pil_with_crosses, CITIES)
            draw_subsolar_point_on_pil(pil_with_crosses, now)
            draw_sublunar_point_on_pil(pil_with_crosses, now)
            current_surface = pil_to_pygame_surface(pil_with_crosses)
            last_dt = now

        # draw centered with black background
        screen.fill((0,0,0))
        screen.blit(current_surface, (offset_x, offset_y))
        pygame.display.flip()

        clock.tick(UPDATE_FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
