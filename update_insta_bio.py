"""
Instagram Bio Day Counter
Updates your Instagram bio daily with a day count from your start date.

Setup:
  python -m pip install selenium undetected-chromedriver python-dotenv

Usage:
  1. Set your START_DATE and BIO_TEMPLATE below
  2. Set your Instagram username and password below
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

# Your Instagram credentials
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


def update_instagram_bio(username, password, new_bio):
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")


    driver = uc.Chrome(
        options=options,
        version_main=149,
        use_subprocess=True
    )

    wait = WebDriverWait(driver, 20)

    try:
        print("🔐 Logging in to Instagram...")
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(4)

        try:
            cookie_btn = driver.find_element(
                By.XPATH,
                "//button[contains(text(),'Allow') or contains(text(),'Accept')]"
            )
            cookie_btn.click()
            time.sleep(1)
        except Exception:
            pass

        
        username_field = wait.until(
            EC.presence_of_element_located((By.NAME, "email"))
            )

        username_field.clear()
        username_field.send_keys(username)
        time.sleep(0.5)

        password_field = driver.find_element(By.NAME, "pass")
        password_field.clear()
        password_field.send_keys(password)
        time.sleep(1)

        password_field.send_keys(Keys.RETURN)
        time.sleep(5)

        try:
            not_now = driver.find_element(
                By.XPATH,
                "//button[contains(text(),'Not now') or contains(text(),'Not Now')]"
            )
            not_now.click()
            time.sleep(2)
        except Exception:
            pass

        try:
            not_now = driver.find_element(
                By.XPATH,
                "//button[contains(text(),'Not now') or contains(text(),'Not Now')]"
            )
            not_now.click()
            time.sleep(2)
        except Exception:
            pass

        print("✏️ Navigating to Edit Profile...")
        driver.get("https://www.instagram.com/accounts/edit/")
        time.sleep(4)

        
        bio_field = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//textarea[@placeholder='Bio']")
            )
        )
        

        bio_field.click()
        time.sleep(0.5)

        bio_field.send_keys(Keys.CONTROL + "a")
        time.sleep(0.3)

        bio_field.send_keys(Keys.DELETE)
        time.sleep(0.3)

        for char in new_bio:
            bio_field.send_keys(char)
            time.sleep(0.02)

        time.sleep(1)

        submit_btn = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//div[@role='button' and text()='Submit']")
            )
        )

        driver.execute_script("arguments[0].click();", submit_btn)
        print(f"✅ Bio updated successfully to: {new_bio}")
        return True

    except Exception as e:
            import traceback

            
            print("\n===== FULL ERROR =====")
            print(type(e).__name__)
            print(str(e))
            traceback.print_exc()
            print("======================\n")

            return False



    finally:
        driver.quit()



if __name__ == "__main__":
    days = calculate_days()
    bio = build_bio(days)

    print(f"📅 Today is day {days} since {START_DATE}")
    print(f"📝 New bio will be: {bio}")

    update_instagram_bio(IG_USERNAME, IG_PASSWORD, bio)
