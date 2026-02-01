import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from os import getcwd

# Chrome Options setup
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--use-fake-ui-for-media-stream") # Permission popup bypass
chrome_options.add_argument("--headless=new") # Background me chalane ke liye

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)

# Website path setup
website = f"file:///{getcwd()}/index.html"
driver.get(website)

rec_file = f"{getcwd()}/input.txt"

def listen():
    try:
        wait = WebDriverWait(driver, 20)

        # Start button click karein
        start_button = wait.until(
            EC.element_to_be_clickable((By.ID, "startButton"))
        )
        start_button.click()
        print("🎤 Listening started... (Speak now)")

        while True:
            # Output element ko dhundhe
            output_element = wait.until(
                EC.presence_of_element_located((By.ID, "output"))
            )

            current_text = output_element.text.strip()

            # Agar text khali nahi hai, to process karein
            if current_text:
                
                # File me likhein
                with open(rec_file, "w", encoding="utf-8") as f:
                    f.write(current_text.lower())

                print("Friday :", current_text)

                # IMPORTANT: Process karne ke baad browser se text clear kar dein
                # Taaki agli baar same text dubara read na ho
                driver.execute_script("arguments[0].innerText = '';", output_element)

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("⛔ Stopped by user")
    except Exception as e:
        print("❌ Error :", e)
    finally:
        driver.quit()

if __name__ == "__main__":
    listen()