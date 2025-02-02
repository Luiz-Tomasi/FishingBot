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

def minigame():
  sleep(0.2)
  my_keyboard.key_down(0x39)
  my_keyboard.release_key(0x39)
  fish = True
  while fish !=None:
    try :
      # Tirar screenshot da região do minijogo
      screenshot = pyautogui.screenshot(region=MINIGAME_REGION)
      screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGR2GRAY)

      fish = find_fish('peixe.png', screenshot)
    except Exception as e:
       fish = None
       print(f"Peixe detectado em {fish}")

    try:
      bar = pyautogui.locateOnScreen('barra.png', confidence=0.8, region=MINIGAME_REGION)
    except pyautogui.ImageNotFoundException:
      bar = None



    if bar is not None and fish is not None:
      print(f"Barra: { bar } ")
      print(f"Mini-peixe detectado: { fish[1] }")
      if fish[1] + 50 < bar.top + 50:
        print("Pressionando tecla...")
        my_keyboard.key_down(0x39)
      else:
        print("Soltando tecla...")
        my_keyboard.release_key(0x39)
    else:
      print("Nenhum dos dois detectados, mantendo tecla pressionada brevemente...")
      my_keyboard.key_down(0x39)

    if bar is None and fish is None:
      print("Não tem minigame")
      break

def attack():
  my_attacks = ['f5', 'f6', 'f7', 'f8', 'F9']
  for attack in my_attacks:
    sleep(0.2)
    my_keyboard.press(attack)

keyboard.wait('h')
while True:
  print('Iniciando pesca')
  fishing_position = set_fishing_rod()
  wait_bubble(fishing_position)
  minigame()
  attack()
  sleep(5)
  my_keyboard.press('F12')