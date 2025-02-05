import tkinter as tk
from tkinter import scrolledtext
import threading
import time
import pyautogui
import random
from time import sleep
import my_keyboard
import keyboard
import cv2
import numpy as np

FISHING_POSITIONS = [(909, 196)]
IMG_BUBBLE_SIZE = (120, 120)
MINIGAME_REGION = (938, 487, 29, 355)

def set_fishing_rod():
    area = random.choice(FISHING_POSITIONS)
    center_area = pyautogui.center(area + IMG_BUBBLE_SIZE)
    pyautogui.moveTo(center_area)
    pyautogui.click(button='left')  # Adicionado clique com o botão esquerdo do mouse
    sleep(0.5)
    my_keyboard.press('caps')
    return area

def wait_bubble(fishing_position):
    while True:
        try:
            bubble = pyautogui.locateOnScreen('bubble2.png', confidence=0.7)
        except pyautogui.ImageNotFoundException as e:
            bubble = None
        if bubble != None:
            my_keyboard.press('caps')
            break

def find_fish(image_path, screenshot):
    fish_template = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    result = cv2.matchTemplate(screenshot, fish_template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    confidence_threshold = 0.65
    if max_val >= confidence_threshold:
        return max_loc
    return None

def find_bar(image_path, screenshot):
    bar_template = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    result = cv2.matchTemplate(screenshot, bar_template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    confidence_threshold = 0.65
    if max_val >= confidence_threshold:
        return max_loc
    return None

def minigame():
    sleep(0.2)
    my_keyboard.key_down(0x39)
    my_keyboard.release_key(0x39)

    fish_location = None
    bar_location = None
    no_detection_count = 0
    estado = 0
    estados_repetindo_count = 0
    while no_detection_count < 50 and estados_repetindo_count < 80:
        try:
            screenshot = pyautogui.screenshot(region=MINIGAME_REGION)
            screenshot_cv2 = cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGR2GRAY)

            new_fish_location = find_fish('peixe.png', screenshot_cv2)
            new_bar_location = find_bar('barra.png', screenshot_cv2)

            if new_fish_location:
                fish_location = new_fish_location
            if new_bar_location:
                bar_location = new_bar_location

            if fish_location and bar_location:
                no_detection_count = 0

                fish_y = fish_location[1]
                bar_y = bar_location[1]

                print(f"Posição do peixe: {fish_y}, Posição da barra: {bar_y}")

                if fish_y < bar_y:
                    if estado == 1:
                        estados_repetindo_count += 1
                    else:
                        estados_repetindo_count = 0
                    estado = 1
                    my_keyboard.key_down(0x39)
                elif fish_y > bar_y + 35:
                    if estado == 2:
                        estados_repetindo_count += 1
                    else:
                        estados_repetindo_count = 0
                    estado = 2
                    my_keyboard.release_key(0x39)
                else:
                    if estado == 3:
                        estados_repetindo_count += 1
                    else:
                        estados_repetindo_count = 0
                    estado = 3
            else:
                no_detection_count += 1
        except Exception as e:
            print(f"Erro no minigame: {e}")
            break

    my_keyboard.release_key(0x39)

def attack():
    my_attacks = ['f4','f5', 'f6', 'f7', 'f8', 'F9']
    for attack in my_attacks:
        sleep(0.2)
        my_keyboard.press(attack)

def isHungry():
    screenshot = pyautogui.screenshot(region=MINIGAME_REGION)
    screenshot_cv2 = cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGR2GRAY)

    isHungry = find_fish('fome.png', screenshot_cv2)
    if isHungry != None:
        my_keyboard.press('F11')

# Funções para controle do bot
def start_bot():
    global bot_running
    bot_running = True
    log("Bot iniciado.")
    threading.Thread(target=run_bot, daemon=True).start()

def stop_bot():
    global bot_running
    bot_running = False
    log("Bot parado.")

def run_bot():
    while bot_running:
        try:
            log("Iniciando pesca...")
            fishing_position = set_fishing_rod()
            wait_bubble(fishing_position)
            minigame()
            isHungry()
            attack()
            log("Pescando...")
            sleep(7)
            my_keyboard.press('F12')
        except Exception as e:
            log(f"Erro: {e}")
            break

def log(message):
    log_box.config(state=tk.NORMAL)
    log_box.insert(tk.END, f"{message}\n")
    log_box.yview(tk.END)
    log_box.config(state=tk.DISABLED)

# Criar janela principal
window = tk.Tk()
window.title("Fishing Bot")
window.geometry("400x400")
window.attributes('-topmost', True)  # Define prioridade sobre outras janelas

# Botões para iniciar e parar o bot
start_button = tk.Button(window, text="Iniciar Bot", command=start_bot, bg="green", fg="white")
start_button.pack(pady=10)

stop_button = tk.Button(window, text="Parar Bot", command=stop_bot, bg="red", fg="white")
stop_button.pack(pady=10)

# Caixa de texto para logs
log_box = scrolledtext.ScrolledText(window, width=70, height=20, state=tk.DISABLED, wrap=tk.WORD)
log_box.pack(pady=10)

# Variável de controle do bot
bot_running = False

def on_close():
    global bot_running
    bot_running = False
    window.destroy()

window.protocol("WM_DELETE_WINDOW", on_close)
window.mainloop()
