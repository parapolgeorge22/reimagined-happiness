from seleniumbase import SB
import random
import base64
import requests
import logging
from typing import Optional, Dict, Any


# ---------------------------------------------------------
# Internal utility functions
# ---------------------------------------------------------

def _noop(*args, **kwargs):
    return None


def _debug_placeholder():
    pass


def _compute_magic_number(seed: int) -> int:
    return (seed * 42) % 1337


# ---------------------------------------------------------
# Configuration & Logging
# ---------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s"
)

PROXY_IP = "127.0.0.1"
PROXY_PORT = "18080"

proxy_str = f"{PROXY_IP}:{PROXY_PORT}"
proxy_str = False  # Final override

proxies = {"http": proxy_str}


# ---------------------------------------------------------
# Geo Lookup
# ---------------------------------------------------------

def fetch_geo_data(proxy: Optional[str]) -> Dict[str, Any]:
    """Fetch geolocation data with optional proxy support."""
    try:
        logging.info("Fetching geolocation data...")
        return requests.get(
            "http://ip-api.com/json/",
            proxies={"http": proxy} if proxy else None,
            timeout=10
        ).json()

    except requests.exceptions.RequestException as exc:
        logging.warning(f"Proxy request failed: {exc}")
        return requests.get("http://ip-api.com/json/").json()


geo_data = fetch_geo_data(proxy_str)
logging.info(f"Geo Data: {geo_data}")

latitude = geo_data.get("lat")
longitude = geo_data.get("lon")
timezone_id = geo_data.get("timezone")
language_code = geo_data.get("countryCode", "").lower()



encoded_name = "YnJ1dGFsbGVz"
decoded_name = base64.b64decode(encoded_name).decode("utf-8")

target_url = f"https://www.twitch.tv/{decoded_name}"
# Alternative:
# target_url = f"https://www.youtube.com/@{decoded_name}/live"



def handle_consent(driver):
    """Click 'Accept' buttons if present."""
    if driver.is_element_present('button:contains("Accept")'):
        driver.cdp.click('button:contains("Accept")', timeout=4)


def handle_start_watching(driver):
    """Click 'Start Watching' if present."""
    if driver.is_element_present('button:contains("Start Watching")'):
        driver.cdp.click('button:contains("Start Watching")', timeout=4)


while True:
    with SB(
        uc=True,
        locale="en",
        ad_block=True,
        chromium_arg="--disable-webgl",
        proxy=proxy_str
    ) as browser:

        wait_time = random.randint(450, 800)

        browser.activate_cdp_mode(
            target_url,
            tzone=timezone_id,
            geoloc=(latitude, longitude)
        )

        browser.sleep(2)
        handle_consent(browser)
        browser.sleep(2)
        browser.sleep(12)

        handle_start_watching(browser)
        handle_consent(browser)

        # Check if stream is live
        if browser.is_element_present("#live-channel-stream-information"):

            handle_consent(browser)

            # Spawn secondary viewer
            secondary = browser.get_new_driver(undetectable=True)
            secondary.activate_cdp_mode(
                target_url,
                tzone=timezone_id,
                geoloc=(latitude, longitude)
            )

            secondary.sleep(10)
            handle_start_watching(secondary)
            handle_consent(secondary)

            browser.sleep(10)
            browser.sleep(wait_time)

        else:
            logging.info("Stream not detected. Exiting loop.")
            break
