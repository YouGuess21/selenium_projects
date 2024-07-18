import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys  
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
import os
import time
import threading
import hashlib

stop_flag = False
PASS_HASH = "0eeb54464bc2486f985b3c95432f80732149bc9960d40a045cb3fb980f8f14b2"
print(PASS_HASH)
in_pass = input("Enter password for the web-site (be checked against the above hash):")
input_hash = hashlib.sha256(in_pass.encode()).hexdigest()
if input_hash != PASS_HASH:
    print("WRONG!")
    exit()

def create_log_file(base_name, village, redate):
    counter = 1
    while True:
        filename = f"{base_name}_{village}_{redate}_{counter}.txt"
        if not os.path.exists(filename):
            return open(filename, "w")
        counter += 1

def is_select_button_clickable(driver, campaign_id):
    try:
        select_button = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.XPATH, f"//button[@type='submit' and @name='{campaign_id}' and contains(@class, 'btn-primary')]"))
        )
        return select_button
    except:
        return None

def login(driver, inp_pass):
    driver.get("https://bharatpashudhan.ndlm.co.in/auth/login")
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'section.login-section'))
    )
    username = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="username"]'))
    )
    username.send_keys(inp_pass) # add username
    password = driver.find_element(By.CSS_SELECTOR, 'input[name="password"]')
    password.send_keys(inp_pass) # add password
    login_button = driver.find_element(By.CSS_SELECTOR, 'button.mat-button')
    login_button.click()
    WebDriverWait(driver, 20).until(EC.url_changes("https://bharatpashudhan.ndlm.co.in/auth/login"))

def setup_driver():
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
    driver.maximize_window()
    return driver

def run_automation(village_name, file_path, start_row, end_row, date, campaign_id):
    global stop_flag
    try:
        df = pd.read_excel(file_path, sheet_name=village_name, header=0, skiprows=start_row-2, nrows=end_row-start_row+1)
        owner_ids = df.iloc[:, 0].tolist()

        driver = setup_driver()
        login(driver, in_pass)

        redate = date.replace('/','_')
        log_file = create_log_file("logs", village_name, redate)

        driver.get("https://bharatpashudhan.ndlm.co.in/dashboard/vaccination")
        
        flag = 0

        for owner_id in owner_ids:
            if stop_flag:
                break  # Check if stop button has been pressed
            
            current_owner_var.set(f"Processing Owner ID: {owner_id}")
            window.update_idletasks()

            try: 
                time.sleep(2)
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//*[@id='carousel-control-next']"))
                )       
                
                if flag != 1:
                    while True:
                        next_button.click()
                        select_button = is_select_button_clickable(driver, campaign_id)
                        if select_button:
                            select_button.click()
                            break
                        time.sleep(1)

                time.sleep(10)
                select_village_dropdown = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '#selectVillage .ng-select-container'))
                )
                select_village_dropdown.click()
                actions = ActionChains(driver)
                actions.send_keys(village_name)
                actions.perform()
                actions.send_keys(Keys.ENTER)
                actions.perform()

                search_input = driver.find_element(By.ID, 'search-by')
                search_input.clear()
                search_input.send_keys(owner_id)
                search_button = driver.find_element(By.XPATH, '//button[contains(text(), "Search")]')
                search_button.click()
                time.sleep(2)

                try:
                    alert_dialog = WebDriverWait(driver, 5).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, 'p.alert-content'))
                    )
                    if alert_dialog.text.strip() == 'Animal Not Found For Selected Details':
                        okay_button = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, '//button[@mat-dialog-close and contains(text(), "Okay")]'))
                        )
                        okay_button.click()
                        output = f"Animal not found for owner {owner_id}. Skipped.\n"
                        print(output)
                        log_file.write(output)
                        flag = 1
                        continue
                except:
                    pass

                flag = 0

                proceed_button = WebDriverWait(driver, 40).until(
                    EC.element_to_be_clickable((By.XPATH, '//button[@class="btn btn-primary" and contains(text(), "Proceed")]'))
                )
                driver.execute_script("arguments[0].scrollIntoView();", proceed_button)

                checkboxes = driver.find_elements(By.XPATH, '//input[@type="checkbox" and @id="selectrow"]')
                for checkbox in checkboxes:
                    driver.execute_script("arguments[0].click();", checkbox)

                proceed_button.click()
                time.sleep(5)
                date_input = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH, '//input[@formcontrolname="vaccinationDate"]'))
                )
                date_input.click()
                date_input.send_keys(Keys.CONTROL, 'a')
                date_input.send_keys(Keys.BACKSPACE)
                date_input.send_keys(date)

                submit_button = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, '//button[@class="btn btn-primary" and contains(text(), "Submit")]'))
                )
                submit_button.click()
                try:
                    okay_button = WebDriverWait(driver, 15).until(
                        EC.element_to_be_clickable((By.XPATH, '//button[@class="btn btn-primary" and contains(text(), "Okay")]'))
                    )
                    okay_button = driver.find_element(By.XPATH, '//button[@class="btn btn-primary" and contains(text(), "Okay")]')
                    okay_button.click()
                    output = f"{owner_id} of village {village_name} known errored with date {date}\n"
                    print(output)
                    log_file.write(output)
                    driver.get("https://bharatpashudhan.ndlm.co.in/dashboard/vaccination")
                    continue
                except:
                    ok_button = WebDriverWait(driver, 30).until(
                        EC.element_to_be_clickable((By.XPATH, '//button[@class="btn btn-primary" and contains(text(), "OK")]'))
                    )
                    ok_button.click()
                
                output = f"{owner_id} of village {village_name} done with date {date}\n"
                print(output)
                log_file.write(output)
                time.sleep(3)
            
            except Exception as e:
                output = f"{owner_id} of village {village_name} errored with date {date}. Error: {e}\n"
                print(output)
                log_file.write(output)

                driver.quit()
                driver = setup_driver()
                login(driver)
                driver.get("https://bharatpashudhan.ndlm.co.in/dashboard/vaccination")
                continue
            
        messagebox.showinfo("Processing Complete", "Automation process completed successfully!")
    
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
    
    finally:
        driver.quit()
        log_file.close()

def start_automation():
    global stop_flag
    stop_flag = False  # Reset stop flag
    village_name = village_var.get()
    file_path = file_path_entry.get()
    start_row = int(start_row_entry.get())
    end_row = int(end_row_entry.get())
    date = date_entry.get()
    campaign_id = int(campaign_id_entry.get())
    
    # Run automation in a separate thread
    automation_thread = threading.Thread(target=run_automation, args=(village_name, file_path, start_row, end_row, date, campaign_id))
    automation_thread.start()

def stop_automation():
    global stop_flag
    stop_flag = True
    messagebox.showinfo("Stopping Automation", "Stopping automation... Please wait.")


window = tk.Tk()
window.title("Selenium Automation with Tkinter")
window.geometry("400x400")

tk.Label(window, text="Village Name:").grid(row=0, column=0, padx=10, pady=10)
village_var = tk.StringVar()
village_names = ['Anjankheda', 'Asola Jahagir', 'Bhatumra', 'Bramhanwada', 'Chikhali Bk.', 'Chikhali Kh.', 'Dodki', 'Falegaon Thet', 'Giwha', 'Jambhrun Bhite', 'Jambhrun Naoji', 'Kakaddati', 'Kamathwada', 'Mohgawhan Dube', 'Panchala', 'Sonkhas', 'Surkandi', 'Waghjali', 'Washim (M Cl)', 'Zakalwadi']
village_dropdown = ttk.Combobox(window, textvariable=village_var, values=village_names)
village_dropdown.grid(row=0, column=1, padx=10, pady=10)


tk.Label(window, text="Excel File Path:").grid(row=1, column=0, padx=10, pady=10)
file_path_entry = tk.Entry(window)
file_path_entry.grid(row=1, column=1, padx=10, pady=10)

tk.Label(window, text="Start Row:").grid(row=2, column=0, padx=10, pady=10)
start_row_entry = tk.Entry(window)
start_row_entry.grid(row=2, column=1, padx=10, pady=10)

tk.Label(window, text="End Row:").grid(row=3, column=0, padx=10, pady=10)
end_row_entry = tk.Entry(window)
end_row_entry.grid(row=3, column=1, padx=10, pady=10)

tk.Label(window, text="Date (MM/DD/YYYY):").grid(row=4, column=0, padx=10, pady=10)
date_entry = tk.Entry(window)
date_entry.grid(row=4, column=1, padx=10, pady=10)

tk.Label(window, text="Campaign ID:").grid(row=5, column=0, padx=10, pady=10)
campaign_id_entry = tk.Entry(window)
campaign_id_entry.grid(row=5, column=1, padx=10, pady=10)

current_owner_var = tk.StringVar()
current_owner_var.set("No Owner ID is being processed.")
current_owner_label = tk.Label(window, textvariable=current_owner_var)
current_owner_label.grid(row=6, column=0, columnspan=2, padx=10, pady=10)

def select_file():
    file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx;*.xls")])
    file_path_entry.delete(0, tk.END)
    file_path_entry.insert(tk.END, file_path)

select_file_button = tk.Button(window, text="Select Excel File", command=select_file)
select_file_button.grid(row=1, column=2, padx=10, pady=10)

start_button = tk.Button(window, text="Start Automation", command=start_automation)
start_button.grid(row=7, column=0, padx=10, pady=10)

stop_button = tk.Button(window, text="Stop Automation", command=stop_automation)
stop_button.grid(row=7, column=1, padx=10, pady=10)

window.mainloop()
