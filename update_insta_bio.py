"""
Instagram Bio Day Counter
Updates your Instagram bio daily with a day count from your start date.

Setup:
  python -m pip install selenium undetected-chromedriver python-dotenv

Usage:
  1. Set your START_DATE and BIO_TEMPLATE below
  2. Set IG_USERNAME / IG_PASSWORD in a .env file or GitHub Secrets
  3. Run: python update_insta_bio.py
"""

from dotenv import load_dotenv
import os
import time
import datetime
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

# ── CONFIGURE THESE ──────────────────────────────────────────────────────────

load_dotenv()

IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")

# The date you want to start counting from (YYYY, MM, DD)
START_DATE = datetime.date(2007, 4, 3)

# Your bio template — {days} will be replaced with the day count
BIO_TEMPLATE = "{days}"

# ─────────────────────────────────────────────────────────────────────────────


def calculate_days():
    today = datetime.date.today()
    delta = today - START_DATE
    return delta.days + 1


def build_bio(days):
    return BIO_TEMPLATE.format(days=days)


def save_debug_snapshot(driver, name):
    """Save page source and a note about current URL for debugging."""
    try:
        with open(f"{name}.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"📸 Saved debug snapshot: {name}.html  |  URL: {driver.current_url}")
    except Exception as e:
        print(f"Could not save snapshot {name}: {e}")


def wait_for_login(driver, timeout=15):
    """
    Returns True if we end up on a logged-in page, False otherwise.
    Instagram redirects to /accounts/onetap/ or the feed after successful login.
    """
    end_time = time.time() + timeout
    while time.time() < end_time:
        url = driver.current_url
        # Still on login page → keep waiting
        if "accounts/login" in url:
            time.sleep(1)
            continue
        # Challenge / suspicious login screen
        if "challenge" in url or "checkpoint" in url:
            print("⚠️  Instagram triggered a challenge/checkpoint. Manual intervention needed.")
            save_debug_snapshot(driver, "challenge_page")
            return False
        # Two-factor auth
        if "two_factor" in url or "two-factor" in url:
            print("⚠️  Two-factor authentication required. Disable 2FA or handle it manually.")
            save_debug_snapshot(driver, "2fa_page")
            return False
        # Looks like we're logged in
        print(f"✅ Login appears successful. Current URL: {url}")
        return True
    print("❌ Timed out waiting for post-login redirect.")
    save_debug_snapshot(driver, "login_timeout")
    return False


def update_instagram_bio(username, password, new_bio):
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,900")

    driver = uc.Chrome(
        options=options,
        # Remove version_main so undetected-chromedriver auto-detects
        # the installed Chrome version on the runner
        use_subprocess=True,
    )

    wait = WebDriverWait(driver, 20)

    try:
        # ── 1. Log in ──────────────────────────────────────────────────────
        print("🔐 Logging in to Instagram...")
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(4)

        # Save the raw login page for debugging
        with open("page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("Saved login page source → page.html")
        print(f"Login page URL: {driver.current_url}  |  Title: {driver.title}")

        # Dismiss cookie banner if present
        try:
            cookie_btn = driver.find_element(
                By.XPATH,
                "//button[contains(text(),'Allow') or contains(text(),'Accept')]"
            )
            cookie_btn.click()
            time.sleep(1)
        except Exception:
            pass

        # Type credentials
        username_field = wait.until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        username_field.clear()
        username_field.send_keys(username)
        time.sleep(0.5)

        password_field = driver.find_element(By.NAME, "password")
        password_field.clear()
        password_field.send_keys(password)
        time.sleep(1)

        password_field.send_keys(Keys.RETURN)

        # ── 2. Confirm we are actually logged in ───────────────────────────
        if not wait_for_login(driver):
            return False

        time.sleep(3)

        # Dismiss "Save your login info?" or "Turn on notifications?" prompts
        for _ in range(2):
            try:
                not_now = driver.find_element(
                    By.XPATH,
                    "//button[contains(text(),'Not now') or contains(text(),'Not Now')]"
                )
                not_now.click()
                time.sleep(2)
            except Exception:
                pass

        # ── 3. Navigate to Edit Profile ────────────────────────────────────
        print("✏️  Navigating to Edit Profile...")
        driver.get("https://www.instagram.com/accounts/edit/")
        time.sleep(5)

        save_debug_snapshot(driver, "edit_profile_page")

        # ── 4. Find the bio field ──────────────────────────────────────────
        # Instagram has used different element types over time; try them all.
        bio_field = None
        selectors = [
            (By.XPATH, "//textarea[@placeholder='Bio']"),
            (By.XPATH, "//textarea[contains(@aria-label,'Bio')]"),
            (By.XPATH, "//textarea[@id='pepBio']"),
            # New React-based edit form (as of ~2024–2025)
            (By.XPATH, "//div[@aria-label='Bio'][@contenteditable='true']"),
            (By.XPATH, "//div[@contenteditable='true'][contains(@class,'bio')]"),
            (By.CSS_SELECTOR, "textarea[name='biography']"),
            (By.CSS_SELECTOR, "[data-testid='bio-input']"),
        ]

        for by, selector in selectors:
            try:
                bio_field = WebDriverWait(driver, 6).until(
                    EC.presence_of_element_located((by, selector))
                )
                print(f"✅ Found bio field with selector: {selector}")
                break
            except Exception:
                continue

        if bio_field is None:
            print("❌ Could not locate the bio field with any known selector.")
            save_debug_snapshot(driver, "bio_field_not_found")
            return False

        # ── 5. Clear and type new bio ──────────────────────────────────────
        bio_field.click()
        time.sleep(0.5)

        # Select all + delete
        bio_field.send_keys(Keys.CONTROL + "a")
        time.sleep(0.3)
        bio_field.send_keys(Keys.DELETE)
        time.sleep(0.3)

        # Type character by character to avoid paste-detection
        for char in new_bio:
            bio_field.send_keys(char)
            time.sleep(0.02)

        time.sleep(1)

        # ── 6. Click Submit ────────────────────────────────────────────────
        submit_selectors = [
            (By.XPATH, "//div[@role='button' and text()='Submit']"),
            (By.XPATH, "//button[text()='Submit']"),
            (By.XPATH, "//button[contains(text(),'Submit')]"),
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.XPATH, "//div[@role='button'][contains(text(),'Save')]"),
            (By.XPATH, "//button[contains(text(),'Save')]"),
        ]

        submit_btn = None
        for by, selector in submit_selectors:
            try:
                submit_btn = WebDriverWait(driver, 6).until(
                    EC.element_to_be_clickable((by, selector))
                )
                print(f"✅ Found submit button with selector: {selector}")
                break
            except Exception:
                continue

        if submit_btn is None:
            print("❌ Could not locate the Submit/Save button.")
            save_debug_snapshot(driver, "submit_button_not_found")
            return False

        driver.execute_script("arguments[0].click();", submit_btn)
        time.sleep(2)

        print(f"✅ Bio updated successfully to: {new_bio}")
        return True

    except Exception as e:
        import traceback
        print("\n===== FULL ERROR =====")
        print(type(e).__name__)
        print(str(e))
        traceback.print_exc()
        save_debug_snapshot(driver, "unexpected_error")
        print("======================\n")
        return False

    finally:
        driver.quit()


if __name__ == "__main__":
    days = calculate_days()
    bio = build_bio(days)

    print(f"📅 Today is day {days} since {START_DATE}")
    print(f"📝 New bio will be: {bio}")

    success = update_instagram_bio(IG_USERNAME, IG_PASSWORD, bio)
    if not success:
        raise SystemExit(1)  # Makes the GitHub Actions step fail visibly