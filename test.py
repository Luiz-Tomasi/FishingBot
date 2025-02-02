import pyautogui

while True:
  try:
    region = pyautogui.locateOnScreen('desafio_regiao.png', confidence=0.8)
    print(region)
  except pyautogui.ImageNotFoundException:
    print('None')