from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import time

def setup_driver():
    
    ublock_crx_path = './ublock.crx'
    chrome_options = webdriver.ChromeOptions()
    # Add the uBlock Origin extension to Chrome
    chrome_options.add_extension(ublock_crx_path)
    
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
    driver.maximize_window()
    return driver

def open_y2meta_tab(driver, video_id):
    base_url = 'https://y2meta.app/en/download-youtube/'
    full_url = base_url + video_id

    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[-1])
    driver.get(full_url)

    # print(f"Opened new tab with URL: {full_url}")
    try:
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div/div/div/div[1]/div/div/div/div[4]/div/div[2]/div/div[1]/table/tbody/tr[1]/td[3]/button'))
        ).click()
        # print("Clicked the first button successfully.")

        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[3]/div[2]/div/div[2]/div[2]/div/a'))
        ).click()
        # print("Clicked the second button successfully.")
    
    except Exception as e:
        print(f"Error interacting with the buttons: {e}")

def get_video_urls(playlist_url):
    driver = setup_driver()
    try:
        driver.get(playlist_url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'contents'))
        )

        last_height = driver.execute_script("return document.documentElement.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(2)  # Wait for new videos to load
            new_height = driver.execute_script("return document.documentElement.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        video_elements = driver.find_elements(By.CSS_SELECTOR, 'ytd-playlist-video-renderer a#thumbnail')
        video_urls = [element.get_attribute('href') for element in video_elements]

    finally:
        driver.quit()

    return video_urls

def download_videos(video_urls):
    driver = setup_driver()
    try:
        for video_url in video_urls:
            video_id = video_url.split('v=')[-1].split('&')[0]
            open_y2meta_tab(driver, video_id)
            time.sleep(5)  # Allow some time for the page to load

            # Optionally, you can close the tab here if needed
            # driver.close()
            # driver.switch_to.window(driver.window_handles[0])
            
    finally:
        driver.quit()

playlist_url = 'https://www.youtube.com/playlist?list=PLot-Xpze53ldVwtstag2TL4HQhAnC8ATf'

video_urls = get_video_urls(playlist_url)
download_videos(video_urls)
