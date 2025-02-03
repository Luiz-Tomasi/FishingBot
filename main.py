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
    my_keyboard.key_down(0x39)  # Pressiona a tecla no início
    my_keyboard.release_key(0x39)

    fish_location = None
    bar_location = None
    no_detection_count = 0  # Contador de falhas consecutivas na detecção
    estado = 0
    estados_repetindo_count = 0
    while no_detection_count < 50 and estados_repetindo_count < 80:  # Define o limite para considerar o fim do minigame
        try:
            
            screenshot = pyautogui.screenshot(region=MINIGAME_REGION)
            screenshot_cv2 = cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGR2GRAY)

            # Detectar barra e peixe
            new_fish_location = find_fish('peixe.png', screenshot_cv2)
            new_bar_location = find_bar('barra.png', screenshot_cv2)

            if new_fish_location:
                fish_location = new_fish_location
            if new_bar_location:
                bar_location = new_bar_location

            if fish_location and bar_location:
                no_detection_count = 0  # Resetar contador se ambos forem encontrados

                fish_y = fish_location[1]
                bar_y = bar_location[1]

                print(f"Posição do peixe: {fish_y}, Posição da barra: {bar_y}")

                if fish_y < bar_y:  # Peixe acima
                    if estado == 1:
                        estados_repetindo_count += 1
                        print(f"estado adicionado. Atual: {estados_repetindo_count}")
                    else:
                        estados_repetindo_count = 0
                    estado = 1
                    print("⬆️ Peixe acima, pressionando tecla...")
                    my_keyboard.key_down(0x39)
                elif fish_y > bar_y + 35:  # Peixe abaixo
                    if estado == 2:
                        estados_repetindo_count += 1
                        print(f"estado adicionado. Atual: {estados_repetindo_count}")
                    else:
                        estados_repetindo_count = 0
                    estado = 2
                    print("⬇️ Peixe abaixo, soltando tecla...")
                    my_keyboard.release_key(0x39)
                else:
                    if estado == 3:
                        estados_repetindo_count += 1
                        print(f"estado adicionado. Atual: {estados_repetindo_count}")
                    else:
                        estados_repetindo_count = 0
                    estado = 3
                    print("✅ Peixe dentro da área da barra, mantendo estado atual.")
            else:
                no_detection_count += 1  # Incrementar contador de falhas
                print(f"⚠️ Detecção falhou ({no_detection_count}/50). Verificando novamente...")

        except Exception as e:
            print(f"Erro no minigame: {e}")
            break

    print("🎣 Minigame encerrado. Continuando...")
    my_keyboard.release_key(0x39)  # Garantir que a tecla é liberada no fim


def attack():
  my_attacks = ['f4','f5', 'f6', 'f7', 'f8', 'F9']
  for attack in my_attacks:
    sleep(0.2)
    my_keyboard.press(attack)

def isHungry():
    try: 
        screenshot = pyautogui.screenshot()
        screenshot_cv2 = cv2.cvtColor(np.array(screenshot))
        
        isHungry = find_fish('fome.png', screenshot_cv2)
    except Exception as e:
        isHungry = None
    
    if isHungry != None:
       print("Está com fome")
       sleep(0.3)
       my_keyboard.press('F11')

keyboard.wait('h')
while True:
  print('Iniciando pesca')
  fishing_position = set_fishing_rod()
  wait_bubble(fishing_position)
  minigame()
  isHungry()
  attack()
  sleep(1.5)
  my_keyboard.press('F12')