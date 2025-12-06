# =============================================================================
# FISHING BOT - Versão Limpa e Organizada
# =============================================================================

# -----------------------------------------------------------------------------
# IMPORTS
# -----------------------------------------------------------------------------
import tkinter as tk
from tkinter import scrolledtext
import threading
import random
from time import sleep
import cv2
import numpy as np
import pyautogui
import keyboard
import winsound
from plyer import notification
from pynput import mouse
import my_keyboard

# =============================================================================
# CONSTANTES
# =============================================================================
IMG_BUBBLE_SIZE = (120, 120)
MINIGAME_REGION = (938, 487, 29, 355)
CONFIDENCE_FISH_BAR = 0.65
CONFIDENCE_SHINY = 0.9
MINIGAME_TIMEOUT = 50
MINIGAME_STATE_REPEAT_LIMIT = 80
FISH_BAR_OFFSET = 35

# =============================================================================
# VARIÁVEIS GLOBAIS
# =============================================================================
FISHING_POSITIONS = []
bot_running = False
shiny_notification_active = False
capture_next_click = False

# =============================================================================
# FUNÇÕES DE DETECÇÃO DE IMAGEM
# =============================================================================
def find_image_on_screen(image_path, screenshot, confidence_threshold):
    """
    Função genérica para encontrar uma imagem em uma screenshot.
    
    Args:
        image_path: Caminho para a imagem template
        screenshot: Screenshot em escala de cinza
        confidence_threshold: Nível mínimo de confiança (0-1)
    
    Returns:
        Localização da imagem encontrada ou None
    """
    template = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    
    if max_val >= confidence_threshold:
        return max_loc
    return None


def find_fish(screenshot):
    """Detecta a posição do peixe no minigame."""
    return find_image_on_screen('peixe.png', screenshot, CONFIDENCE_FISH_BAR)


def find_bar(screenshot):
    """Detecta a posição da barra no minigame."""
    return find_image_on_screen('barra.png', screenshot, CONFIDENCE_FISH_BAR)


def find_shiny(screenshot):
    """Detecta se há um pokémon shiny na tela."""
    return find_image_on_screen('shiny.png', screenshot, CONFIDENCE_SHINY)

# =============================================================================
# FUNÇÕES PRINCIPAIS DO BOT
# =============================================================================
def set_fishing_rod():
    """
    Seleciona aleatoriamente uma posição de pesca e lança a vara.
    
    Returns:
        Área selecionada ou None se não houver posições definidas
    """
    if not FISHING_POSITIONS:
        log("Nenhuma posição de pesca definida!")
        return None
    
    area = random.choice(FISHING_POSITIONS)
    center_area = pyautogui.center(area + IMG_BUBBLE_SIZE)
    pyautogui.moveTo(center_area)
    pyautogui.click(button='left')
    sleep(0.5)
    my_keyboard.press('caps')
    return area


def wait_bubble(fishing_position):
    """Aguarda a aparição da bolha indicando que um peixe mordeu."""
    while True:
        try:
            bubble = pyautogui.locateOnScreen('bubble2.png', confidence=0.7)
            if bubble is not None:
                my_keyboard.press('caps')
                break
        except pyautogui.ImageNotFoundException:
            continue


def minigame():
    """
    Executa o minigame de pesca automaticamente.
    Controla a posição da barra para manter o peixe centralizado.
    """
    sleep(0.2)
    my_keyboard.key_down(0x39)
    my_keyboard.release_key(0x39)
    
    fish_location = None
    bar_location = None
    no_detection_count = 0
    current_state = 0
    state_repeat_count = 0
    
    while no_detection_count < MINIGAME_TIMEOUT and state_repeat_count < MINIGAME_STATE_REPEAT_LIMIT:
        try:
            screenshot = pyautogui.screenshot(region=MINIGAME_REGION)
            screenshot_cv2 = cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGR2GRAY)
            
            new_fish_location = find_fish(screenshot_cv2)
            new_bar_location = find_bar(screenshot_cv2)
            
            # Atualiza as localizações se encontradas
            if new_fish_location:
                fish_location = new_fish_location
            if new_bar_location:
                bar_location = new_bar_location
            
            if fish_location and bar_location:
                no_detection_count = 0
                
                fish_y = fish_location[1]
                bar_y = bar_location[1]
                
                print(f"Posição do peixe: {fish_y}, Posição da barra: {bar_y}")
                
                # Determina a ação com base na posição relativa
                new_state = 0
                if fish_y < bar_y:
                    new_state = 1
                    my_keyboard.key_down(0x39)
                elif fish_y > bar_y + FISH_BAR_OFFSET:
                    new_state = 2
                    my_keyboard.release_key(0x39)
                else:
                    new_state = 3
                
                # Controla repetição de estados
                if new_state == current_state:
                    state_repeat_count += 1
                else:
                    state_repeat_count = 0
                    current_state = new_state
            else:
                no_detection_count += 1
                
        except Exception as e:
            print(f"Erro no minigame: {e}")
            break
    
    my_keyboard.release_key(0x39)


def attack():
    """Executa os ataques selecionados pelo usuário."""
    if not auto_attack_enabled.get():
        return
    
    selected_attacks = [key for key, var in attack_keys.items() if var.get()]
    for attack_key in selected_attacks:
        sleep(0.2)
        my_keyboard.press(attack_key)


def check_hunger():
    """Verifica se o personagem está com fome e come automaticamente."""
    if not auto_eat_enabled.get():
        return
    
    screenshot = pyautogui.screenshot()
    screenshot_cv2 = cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGR2GRAY)
    
    hunger_detected = find_image_on_screen('fome.png', screenshot_cv2, CONFIDENCE_FISH_BAR)
    if hunger_detected:
        my_keyboard.press('F11')


def check_shiny():
    """Verifica se um pokémon shiny foi encontrado e notifica o usuário."""
    global shiny_notification_active
    
    if not auto_shiny_enabled.get() or shiny_notification_active:
        return
    
    screenshot = pyautogui.screenshot()
    screenshot_cv2 = cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGR2GRAY)
    
    shiny_detected = find_shiny(screenshot_cv2)
    if shiny_detected:
        log("🌟 Achou um shiny!")
        shiny_notification_active = True
        
        # Reproduz som de notificação
        try:
            winsound.PlaySound("shiny_sound.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
        except:
            winsound.Beep(1000, 500)  # Fallback se o arquivo não existir
        
        # Exibe notificação
        notification.notify(
            title="Shiny encontrado!",
            message="Um shiny foi detectado!",
            app_name="Fishing Bot",
            timeout=5
        )
        
        # Reseta a notificação após 5 segundos
        threading.Timer(5, reset_shiny_notification).start()


def reset_shiny_notification():
    """Reseta o flag de notificação de shiny."""
    global shiny_notification_active
    shiny_notification_active = False

# =============================================================================
# FUNÇÕES DE CAPTURA DE CLIQUES
# =============================================================================
def on_click(x, y, button, pressed):
    """Callback para capturar cliques do mouse."""
    global capture_next_click
    
    if capture_next_click and pressed:
        FISHING_POSITIONS.append((x, y))
        log(f"✓ Posição adicionada: ({x}, {y})")
        update_position_list()
        capture_next_click = False


def capture_click():
    """Ativa o modo de captura do próximo clique."""
    global capture_next_click
    capture_next_click = True
    log("Aguardando próximo clique...")


def remove_position():
    """Remove a posição selecionada da lista."""
    selected = position_listbox.curselection()
    if selected:
        index = selected[0]
        removed_pos = FISHING_POSITIONS.pop(index)
        update_position_list()
        log(f"✗ Posição removida: {removed_pos}")

# =============================================================================
# FUNÇÕES DE CONTROLE DO BOT
# =============================================================================
def toggle_bot():
    """Alterna entre iniciar e parar o bot."""
    global bot_running
    
    if bot_running:
        bot_running = False
        log("⏸ Bot parado.")
        toggle_button.config(text="Iniciar Bot", bg="green", fg="white")
    else:
        if not FISHING_POSITIONS:
            log("❌ Adicione pelo menos uma posição de pesca antes de iniciar!")
            return
        
        bot_running = True
        log("▶ Bot iniciado.")
        toggle_button.config(text="Parar Bot", bg="red", fg="white")
        threading.Thread(target=run_bot, daemon=True).start()


def run_bot():
    """Loop principal do bot."""
    while bot_running:
        try:
            log("🎣 Iniciando pesca...")
            fishing_position = set_fishing_rod()
            
            if fishing_position:
                wait_bubble(fishing_position)
                minigame()
                check_hunger()
                check_shiny()
                attack()
                log("✓ Pesca completa!")
                sleep(3)
                my_keyboard.press('F12')
        except Exception as e:
            log(f"❌ Erro: {e}")
            break

# =============================================================================
# FUNÇÕES DE INTERFACE
# =============================================================================
def log(message):
    """Adiciona uma mensagem ao log na interface."""
    log_box.config(state=tk.NORMAL)
    log_box.insert(tk.END, f"{message}\n")
    log_box.yview(tk.END)
    log_box.config(state=tk.DISABLED)


def update_position_list():
    """Atualiza a lista de posições na interface."""
    position_listbox.delete(0, tk.END)
    for i, pos in enumerate(FISHING_POSITIONS, 1):
        position_listbox.insert(tk.END, f"{i}. ({pos[0]}, {pos[1]})")


def on_close():
    """Callback para fechar a janela corretamente."""
    global bot_running
    bot_running = False
    keyboard.unhook_all()
    window.destroy()

# =============================================================================
# CONFIGURAÇÃO DA INTERFACE GRÁFICA
# =============================================================================

# Criar janela principal
window = tk.Tk()
window.title("Fishing Bot")
window.geometry("500x700")
window.attributes('-topmost', True)

# Variáveis de controle
auto_eat_enabled = tk.BooleanVar(value=True)
auto_attack_enabled = tk.BooleanVar(value=True)
auto_shiny_enabled = tk.BooleanVar(value=True)

# Variáveis de ataques
attack_keys = {
    f'F{i}': tk.BooleanVar(value=False) for i in range(1, 10)
}

# -----------------------------------------------------------------------------
# Botões de Controle Principal
# -----------------------------------------------------------------------------
toggle_button = tk.Button(
    window,
    text="Iniciar Bot",
    command=toggle_bot,
    bg="green",
    fg="white",
    font=("Arial", 12, "bold"),
    height=2
)
toggle_button.pack(pady=10)

capture_button = tk.Button(
    window,
    text="Capturar Próximo Clique",
    command=capture_click,
    bg="blue",
    fg="white",
    font=("Arial", 10)
)
capture_button.pack(pady=5)

# -----------------------------------------------------------------------------
# Lista de Posições de Pesca
# -----------------------------------------------------------------------------
position_frame = tk.Frame(window)
position_frame.pack(pady=10)

tk.Label(position_frame, text="Posições de Pesca:", font=("Arial", 10, "bold")).pack()

position_listbox = tk.Listbox(position_frame, width=50, height=5)
position_listbox.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))

remove_button = tk.Button(
    position_frame,
    text="Remover",
    command=remove_position,
    bg="red",
    fg="white"
)
remove_button.pack(side=tk.RIGHT)

# -----------------------------------------------------------------------------
# Opções de Automação
# -----------------------------------------------------------------------------
options_frame = tk.Frame(window)
options_frame.pack(pady=10)

tk.Checkbutton(
    options_frame,
    text="🍖 Comer automaticamente",
    variable=auto_eat_enabled,
    font=("Arial", 9)
).pack(anchor="w")

tk.Checkbutton(
    options_frame,
    text="⚔️ Atacar automaticamente",
    variable=auto_attack_enabled,
    font=("Arial", 9)
).pack(anchor="w")

tk.Checkbutton(
    options_frame,
    text="✨ Detectar shiny",
    variable=auto_shiny_enabled,
    font=("Arial", 9)
).pack(anchor="w")

# -----------------------------------------------------------------------------
# Seleção de Ataques
# -----------------------------------------------------------------------------
attack_frame = tk.Frame(window)
attack_frame.pack(pady=10)

tk.Label(attack_frame, text="Ataques:", font=("Arial", 10, "bold")).pack()

attack_checkboxes_frame = tk.Frame(attack_frame)
attack_checkboxes_frame.pack()

for key, var in attack_keys.items():
    tk.Checkbutton(
        attack_checkboxes_frame,
        text=key,
        variable=var
    ).pack(side=tk.LEFT, padx=2)

# -----------------------------------------------------------------------------
# Caixa de Logs
# -----------------------------------------------------------------------------
tk.Label(window, text="Log:", font=("Arial", 10, "bold")).pack()

log_box = scrolledtext.ScrolledText(
    window,
    width=60,
    height=12,
    state=tk.DISABLED,
    wrap=tk.WORD,
    font=("Consolas", 9)
)
log_box.pack(pady=5, padx=10)

# =============================================================================
# INICIALIZAÇÃO
# =============================================================================

# Iniciar listener do mouse
mouse_listener = mouse.Listener(on_click=on_click)
mouse_listener.start()

# Configurar atalho de teclado
keyboard.add_hotkey('h', toggle_bot)

# Configurar evento de fechamento da janela
window.protocol("WM_DELETE_WINDOW", on_close)

# Mensagem inicial
log("="*60)
log("Fishing Bot Iniciado!")
log("Tecla H: Ligar/Desligar bot")
log("="*60)

# Iniciar aplicação
window.mainloop()
