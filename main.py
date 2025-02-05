import tkinter as tk
from tkinter import scrolledtext
import threading
import time
import pyautogui
import random
from time import sleep
import my_keyboard
import keyboard  # Biblioteca para detectar pressionamento de teclas
import cv2
import numpy as np
from plyer import notification  # Para notificações
import winsound  # Para reproduzir som
from pynput import mouse  # Para capturar cliques do mouse

# Criar janela principal
window = tk.Tk()
window.title("Fishing Bot")
window.geometry("500x700")  # Aumentei a altura para acomodar a lista de posições
window.attributes('-topmost', True)  # Define prioridade sobre outras janelas

# Variáveis de controle para as funções de comer, atacar e shiny
auto_eat_enabled = tk.BooleanVar(value=True)  # Ativado por padrão
auto_attack_enabled = tk.BooleanVar(value=True)  # Ativado por padrão
auto_shiny_enabled = tk.BooleanVar(value=True)  # Ativado por padrão

# Variáveis para armazenar os ataques selecionados
attack_keys = {
    'F1': tk.BooleanVar(value=False),
    'F2': tk.BooleanVar(value=False),
    'F3': tk.BooleanVar(value=False),
    'F4': tk.BooleanVar(value=False),
    'F5': tk.BooleanVar(value=False),
    'F6': tk.BooleanVar(value=False),
    'F7': tk.BooleanVar(value=False),
    'F8': tk.BooleanVar(value=False),
    'F9': tk.BooleanVar(value=False),
}

# Lista de posições para a vara de pesca
FISHING_POSITIONS = []

IMG_BUBBLE_SIZE = (120, 120)
MINIGAME_REGION = (938, 487, 29, 355)

# Variável para controlar se uma notificação de shiny está aberta
shiny_notification_active = False

# Variável para controlar a captura de cliques
capture_next_click = False

def set_fishing_rod():
    if FISHING_POSITIONS:  # Verifica se há posições na lista
        area = random.choice(FISHING_POSITIONS)
        center_area = pyautogui.center(area + IMG_BUBBLE_SIZE)
        pyautogui.moveTo(center_area)
        pyautogui.click(button='left')  # Adicionado clique com o botão esquerdo do mouse
        sleep(0.5)
        my_keyboard.press('caps')
        return area
    else:
        log("Nenhuma posição de pesca definida!")
        return None

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

def find_shiny(image_path, screenshot):
    bar_template = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    result = cv2.matchTemplate(screenshot, bar_template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    confidence_threshold = 0.9
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
    if auto_attack_enabled.get():  # Verifica se a função de ataque está ativada
        # Obtém as teclas de ataque selecionadas pelo usuário
        selected_attacks = [key for key, var in attack_keys.items() if var.get()]
        for attack in selected_attacks:
            sleep(0.2)
            my_keyboard.press(attack)

def isHungry():
    if auto_eat_enabled.get():  # Verifica se a função de comer está ativada
        screenshot = pyautogui.screenshot()
        screenshot_cv2 = cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGR2GRAY)

        isHungry = find_fish('fome.png', screenshot_cv2)
        if isHungry != None:
            my_keyboard.press('F11')

def isShiny():
    global shiny_notification_active
    if auto_shiny_enabled.get() and not shiny_notification_active:  # Verifica se a função de shiny está ativada e se não há notificação ativa
        screenshot = pyautogui.screenshot()
        screenshot_cv2 = cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGR2GRAY)

        isShiny = find_shiny('shiny.png', screenshot_cv2)
        if isShiny != None:
            log("Achou um shiny!")
            shiny_notification_active = True

            # Reproduz um som de notificação
            winsound.PlaySound("shiny_sound.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)

            # Exibe uma notificação no canto inferior direito
            notification.notify(
                title="Shiny encontrado!",
                message="Um shiny foi detectado!",
                app_name="Fishing Bot",
                timeout=5  # A notificação fecha após 5 segundos
            )

            # Reseta a notificação após 5 segundos
            threading.Timer(5, reset_shiny_notification).start()

def reset_shiny_notification():
    global shiny_notification_active
    shiny_notification_active = False

# Função para capturar cliques do mouse
def on_click(x, y, button, pressed):
    global capture_next_click, FISHING_POSITIONS
    if capture_next_click and pressed:
        FISHING_POSITIONS.append((x, y))  # Adiciona a posição clicada à lista
        log(f"Posição adicionada: ({x}, {y})")
        update_position_list()  # Atualiza a lista de posições na interface
        capture_next_click = False  # Para de capturar cliques

# Inicia o listener do mouse
mouse_listener = mouse.Listener(on_click=on_click)
mouse_listener.start()

# Função para ativar a captura do próximo clique
def capture_click():
    global capture_next_click
    capture_next_click = True
    log("Aguardando próximo clique...")

# Função para atualizar a lista de posições na interface
def update_position_list():
    position_listbox.delete(0, tk.END)  # Limpa a lista atual
    for pos in FISHING_POSITIONS:
        position_listbox.insert(tk.END, f"({pos[0]}, {pos[1]})")  # Adiciona cada posição à lista

# Função para remover a posição selecionada
def remove_position():
    selected = position_listbox.curselection()  # Obtém o índice da posição selecionada
    if selected:
        FISHING_POSITIONS.pop(selected[0])  # Remove a posição da lista
        update_position_list()  # Atualiza a lista na interface
        log(f"Posição removida: {selected[0] + 1}")

# Funções para controle do bot
def toggle_bot():
    global bot_running
    if bot_running:
        bot_running = False
        log("Bot parado.")
        toggle_button.config(text="Iniciar Bot", bg="green", fg="white")
    else:
        bot_running = True
        log("Bot iniciado.")
        toggle_button.config(text="Parar Bot", bg="red", fg="white")
        threading.Thread(target=run_bot, daemon=True).start()

def run_bot():
    while bot_running:
        try:
            log("Iniciando pesca...")
            fishing_position = set_fishing_rod()
            if fishing_position:
                wait_bubble(fishing_position)
                minigame()
                isHungry()
                isShiny()  # Verifica se encontrou um shiny
                attack()
                log("Pescando...")
                sleep(3)
                my_keyboard.press('F12')
        except Exception as e:
            log(f"Erro: {e}")
            break

def log(message):
    log_box.config(state=tk.NORMAL)
    log_box.insert(tk.END, f"{message}\n")
    log_box.yview(tk.END)
    log_box.config(state=tk.DISABLED)

# Botão para alternar entre iniciar e parar o bot
toggle_button = tk.Button(window, text="Iniciar Bot", command=toggle_bot, bg="green", fg="white")
toggle_button.pack(pady=10)

# Botão para capturar o próximo clique
capture_button = tk.Button(window, text="Capturar Próximo Clique", command=capture_click, bg="blue", fg="white")
capture_button.pack(pady=10)

# Frame para a lista de posições
position_frame = tk.Frame(window)
position_frame.pack(pady=10)

# Listbox para exibir as posições de pesca
position_listbox = tk.Listbox(position_frame, width=50, height=5)
position_listbox.pack(side=tk.LEFT, fill=tk.BOTH)

# Botão para remover a posição selecionada
remove_button = tk.Button(position_frame, text="Remover Selecionado", command=remove_position, bg="red", fg="white")
remove_button.pack(side=tk.RIGHT, padx=10)

# Checkbutton para ativar/desativar a função de comer automaticamente
auto_eat_switch = tk.Checkbutton(
    window,
    text="Comer automaticamente",
    variable=auto_eat_enabled,
    onvalue=True,
    offvalue=False
)
auto_eat_switch.pack(pady=5)

# Checkbutton para ativar/desativar a função de atacar automaticamente
auto_attack_switch = tk.Checkbutton(
    window,
    text="Atacar automaticamente",
    variable=auto_attack_enabled,
    onvalue=True,
    offvalue=False
)
auto_attack_switch.pack(pady=5)

# Checkbutton para ativar/desativar a função de shiny
auto_shiny_switch = tk.Checkbutton(
    window,
    text="Detectar shiny",
    variable=auto_shiny_enabled,
    onvalue=True,
    offvalue=False
)
auto_shiny_switch.pack(pady=5)

# Frame para os checkboxes de seleção de ataques
attack_frame = tk.Frame(window)
attack_frame.pack(pady=10)

tk.Label(attack_frame, text="Selecione os ataques:").pack()

# Adiciona checkboxes para cada tecla de F1 a F9 na mesma linha
for key, var in attack_keys.items():
    tk.Checkbutton(attack_frame, text=key, variable=var, onvalue=True, offvalue=False).pack(side=tk.LEFT, padx=2)

# Caixa de texto para logs
log_box = scrolledtext.ScrolledText(window, width=70, height=20, state=tk.DISABLED, wrap=tk.WORD)
log_box.pack(pady=10)

# Variável de controle do bot
bot_running = False

# Configurar a tecla "H" para alternar o bot
keyboard.add_hotkey('h', toggle_bot)  # Tecla "H" chama a função toggle_bot

def on_close():
    global bot_running
    bot_running = False
    keyboard.unhook_all()  # Remove todos os hooks de teclado ao fechar a janela
    window.destroy()

window.protocol("WM_DELETE_WINDOW", on_close)
window.mainloop()