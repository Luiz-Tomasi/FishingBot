# =============================================================================
# FISHING BOT - Interface Moderna
# =============================================================================

# -----------------------------------------------------------------------------
# IMPORTS
# -----------------------------------------------------------------------------
import tkinter as tk
from tkinter import scrolledtext, ttk
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

# Teclas padrão
DEFAULT_FISHING_KEY = 'caps'
DEFAULT_LOOT_KEY = 'e'
DEFAULT_TARGET_KEY = 'tab'  # TAB é para selecionar alvo
DEFAULT_STOP_POKEMON_KEY = 'ctrl+s'
LOOPS_BEFORE_STOP = 6

# Cores do tema
COLORS = {
    'bg_primary': '#1e1e2e',
    'bg_secondary': '#2a2a3e',
    'bg_tertiary': '#363650',
    'accent_blue': '#89b4fa',
    'accent_green': '#a6e3a1',
    'accent_red': '#f38ba8',
    'accent_yellow': '#f9e2af',
    'accent_purple': '#cba6f7',
    'text_primary': '#cdd6f4',
    'text_secondary': '#a6adc8',
    'success': '#a6e3a1',
    'warning': '#f9e2af',
    'error': '#f38ba8',
}

# =============================================================================
# VARIÁVEIS GLOBAIS
# =============================================================================
FISHING_POSITIONS = []
bot_running = False
shiny_notification_active = False
capture_next_click = False
loop_counter = 0

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
        log("❌ Nenhuma posição de pesca definida!", "error")
        return None
    
    area = random.choice(FISHING_POSITIONS)
    center_area = pyautogui.center(area + IMG_BUBBLE_SIZE)
    pyautogui.moveTo(center_area)
    pyautogui.click(button='left')
    sleep(0.5)
    
    # Usar tecla de pesca configurável
    fishing_key = fishing_key_entry.get().strip() or DEFAULT_FISHING_KEY
    press_key(fishing_key)
    
    return area


def wait_bubble(fishing_position):
    """Aguarda a aparição da bolha indicando que um peixe mordeu."""
    while True:
        try:
            bubble = pyautogui.locateOnScreen('bubble2.png', confidence=0.7)
            if bubble is not None:
                # Usar tecla de pesca configurável
                fishing_key = fishing_key_entry.get().strip() or DEFAULT_FISHING_KEY
                press_key(fishing_key)
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
    
    # Primeiro, selecionar o alvo com TAB
    target_key = target_key_entry.get().strip() or DEFAULT_TARGET_KEY
    sleep(0.2)
    press_key(target_key)
    log(f"🎯 Alvo selecionado (tecla: {target_key})", "info")
    
    # Depois, atacar com as teclas F1-F9 selecionadas
    selected_f_keys = [key for key, var in attack_keys.items() if var.get()]
    
    if selected_f_keys:
        for attack in selected_f_keys:
            sleep(0.2)
            my_keyboard.press(attack)
            log(f"⚔️ Ataque: {attack}", "info")
    else:
        log("⚠️ Nenhum ataque selecionado (F1-F9)", "warning")


def auto_loot():
    """Executa o loot automático se ativado."""
    if not auto_loot_enabled.get():
        return
    
    loot_key = loot_key_entry.get().strip() or DEFAULT_LOOT_KEY
    sleep(0.3)
    press_key(loot_key)
    log(f"💎 Loot executado (tecla: {loot_key})", "info")


def stop_pokemon():
    """Para o pokémon usando a tecla configurada."""
    stop_key = stop_pokemon_key_entry.get().strip() or DEFAULT_STOP_POKEMON_KEY
    sleep(0.3)
    press_key(stop_key)
    log(f"🛑 Pokémon parado (tecla: {stop_key})", "warning")


def press_key(key_combination):
    """
    Pressiona uma tecla ou combinação de teclas.
    Suporta teclas simples ('e', 'tab') e combinações ('ctrl+s', 'shift+a').
    """
    key_combination = key_combination.lower().strip()
    
    # Se for combinação de teclas (contém +)
    if '+' in key_combination:
        parts = [k.strip() for k in key_combination.split('+')]
        
        # Pressionar teclas modificadoras
        for modifier in parts[:-1]:
            if modifier == 'ctrl':
                my_keyboard.key_down(0x1D)  # Ctrl
            elif modifier == 'shift':
                my_keyboard.key_down(0x2A)  # Shift
            elif modifier == 'alt':
                my_keyboard.key_down(0x38)  # Alt
        
        sleep(0.1)
        
        # Pressionar tecla principal
        main_key = parts[-1].upper()
        if main_key in my_keyboard.key:
            my_keyboard.press(main_key)
        else:
            # Tentar pressionar como caractere
            keyboard.press_and_release(main_key)
        
        sleep(0.1)
        
        # Soltar teclas modificadoras
        for modifier in parts[:-1]:
            if modifier == 'ctrl':
                my_keyboard.release_key(0x1D)
            elif modifier == 'shift':
                my_keyboard.release_key(0x2A)
            elif modifier == 'alt':
                my_keyboard.release_key(0x38)
    else:
        # Tecla simples
        key_upper = key_combination.upper()
        if key_upper in my_keyboard.key:
            my_keyboard.press(key_upper)
        else:
            # Usar biblioteca keyboard para teclas não mapeadas
            keyboard.press_and_release(key_combination)


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
        log("🌟 SHINY ENCONTRADO! 🌟", "success")
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
        log(f"✓ Posição adicionada: ({x}, {y})", "success")
        update_position_list()
        update_stats()
        capture_next_click = False


def capture_click():
    """Ativa o modo de captura do próximo clique."""
    global capture_next_click
    capture_next_click = True
    log("🎯 Clique na tela para adicionar posição...", "info")
    capture_button.config(text="⏳ Aguardando clique...", bg=COLORS['accent_yellow'])


def remove_position():
    """Remove a posição selecionada da lista."""
    selected = position_listbox.curselection()
    if selected:
        index = selected[0]
        removed_pos = FISHING_POSITIONS.pop(index)
        update_position_list()
        update_stats()
        log(f"✗ Posição removida: {removed_pos}", "warning")


def clear_positions():
    """Limpa todas as posições de pesca."""
    global FISHING_POSITIONS
    if FISHING_POSITIONS:
        FISHING_POSITIONS = []
        update_position_list()
        update_stats()
        log("🗑️ Todas as posições removidas", "warning")

# =============================================================================
# FUNÇÕES DE CONTROLE DO BOT
# =============================================================================
def toggle_bot():
    """Alterna entre iniciar e parar o bot."""
    global bot_running
    
    if bot_running:
        bot_running = False
        log("⏸ Bot pausado", "warning")
        toggle_button.config(
            text="▶ INICIAR BOT",
            style="Success.TButton"
        )
        status_label.config(text="● PARADO", foreground=COLORS['error'])
    else:
        if not FISHING_POSITIONS:
            log("❌ Adicione pelo menos uma posição de pesca!", "error")
            return
        
        bot_running = True
        log("▶ Bot iniciado", "success")
        toggle_button.config(
            text="⏸ PARAR BOT",
            style="Danger.TButton"
        )
        status_label.config(text="● ATIVO", foreground=COLORS['success'])
        threading.Thread(target=run_bot, daemon=True).start()


def run_bot():
    """Loop principal do bot."""
    global loop_counter
    loop_counter = 0
    
    while bot_running:
        try:
            loop_counter += 1
            log(f"🔄 Loop {loop_counter}/{LOOPS_BEFORE_STOP}", "info")
            log("🎣 Iniciando pesca...", "info")
            
            fishing_position = set_fishing_rod()
            
            if fishing_position:
                wait_bubble(fishing_position)
                minigame()
                check_hunger()
                check_shiny()
                attack()
                auto_loot()  # Loot após ataque
                log("✓ Pesca completa!", "success")
                sleep(3)
                my_keyboard.press('F12')
                
                # Verificar se atingiu o limite de loops
                if loop_counter >= LOOPS_BEFORE_STOP:
                    log(f"⏸ Limite de {LOOPS_BEFORE_STOP} loops atingido, parando pokémon...", "warning")
                    stop_pokemon()
                    loop_counter = 0  # Resetar contador
                    sleep(2)  # Aguardar um pouco antes de continuar
        except Exception as e:
            log(f"❌ Erro: {e}", "error")
            break

# =============================================================================
# FUNÇÕES DE INTERFACE
# =============================================================================
def log(message, level="info"):
    """Adiciona uma mensagem ao log na interface com cores."""
    log_box.config(state=tk.NORMAL)
    
    # Define a cor baseada no nível
    tag = level
    log_box.insert(tk.END, f"{message}\n", tag)
    log_box.yview(tk.END)
    log_box.config(state=tk.DISABLED)


def update_position_list():
    """Atualiza a lista de posições na interface."""
    position_listbox.delete(0, tk.END)
    for i, pos in enumerate(FISHING_POSITIONS, 1):
        position_listbox.insert(tk.END, f"  {i}. ({pos[0]}, {pos[1]})")


def update_stats():
    """Atualiza as estatísticas na interface."""
    positions_count_label.config(text=f"{len(FISHING_POSITIONS)}")


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
window.title("🎣 Fishing Bot Pro")
window.geometry("700x900")
window.configure(bg=COLORS['bg_primary'])
window.resizable(False, False)

# Configurar estilos
style = ttk.Style()
style.theme_use('clam')

# Estilo para botões
style.configure(
    "TButton",
    background=COLORS['bg_tertiary'],
    foreground=COLORS['text_primary'],
    borderwidth=0,
    focuscolor='none',
    font=("Segoe UI", 10),
    padding=10
)

style.configure(
    "Success.TButton",
    background=COLORS['accent_green'],
    foreground=COLORS['bg_primary'],
    font=("Segoe UI", 12, "bold"),
    padding=15
)

style.configure(
    "Danger.TButton",
    background=COLORS['accent_red'],
    foreground=COLORS['bg_primary'],
    font=("Segoe UI", 12, "bold"),
    padding=15
)

style.configure(
    "Accent.TButton",
    background=COLORS['accent_blue'],
    foreground=COLORS['bg_primary'],
    font=("Segoe UI", 10),
    padding=8
)

style.map("TButton",
    background=[('active', COLORS['bg_secondary'])]
)

# Variáveis de controle
auto_eat_enabled = tk.BooleanVar(value=True)
auto_attack_enabled = tk.BooleanVar(value=True)
auto_shiny_enabled = tk.BooleanVar(value=True)
auto_loot_enabled = tk.BooleanVar(value=True)  # Nova opção

# Variáveis de ataques
attack_keys = {
    f'F{i}': tk.BooleanVar(value=False) for i in range(1, 10)
}

# =============================================================================
# HEADER
# =============================================================================
header_frame = tk.Frame(window, bg=COLORS['bg_secondary'], height=80)
header_frame.pack(fill=tk.X, pady=(0, 10))
header_frame.pack_propagate(False)

title_label = tk.Label(
    header_frame,
    text="🎣 FISHING BOT PRO",
    font=("Segoe UI", 24, "bold"),
    bg=COLORS['bg_secondary'],
    fg=COLORS['accent_blue']
)
title_label.pack(pady=10)

status_label = tk.Label(
    header_frame,
    text="● PARADO",
    font=("Segoe UI", 12),
    bg=COLORS['bg_secondary'],
    fg=COLORS['error']
)
status_label.pack()

# =============================================================================
# CONTAINER PRINCIPAL
# =============================================================================
main_container = tk.Frame(window, bg=COLORS['bg_primary'])
main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

# -----------------------------------------------------------------------------
# SEÇÃO: CONTROLE PRINCIPAL
# -----------------------------------------------------------------------------
control_frame = tk.LabelFrame(
    main_container,
    text="  🎮 CONTROLE  ",
    font=("Segoe UI", 11, "bold"),
    bg=COLORS['bg_secondary'],
    fg=COLORS['text_primary'],
    borderwidth=2,
    relief=tk.GROOVE
)
control_frame.pack(fill=tk.X, pady=(0, 10))

button_container = tk.Frame(control_frame, bg=COLORS['bg_secondary'])
button_container.pack(pady=15, padx=15)

toggle_button = ttk.Button(
    button_container,
    text="▶ INICIAR BOT",
    command=toggle_bot,
    style="Success.TButton",
    width=30
)
toggle_button.pack(pady=5)

hotkey_label = tk.Label(
    button_container,
    text="⌨️ Atalho: Tecla H",
    font=("Segoe UI", 9),
    bg=COLORS['bg_secondary'],
    fg=COLORS['text_secondary']
)
hotkey_label.pack(pady=5)

# -----------------------------------------------------------------------------
# SEÇÃO: POSIÇÕES DE PESCA
# -----------------------------------------------------------------------------
positions_frame = tk.LabelFrame(
    main_container,
    text="  📍 POSIÇÕES DE PESCA  ",
    font=("Segoe UI", 11, "bold"),
    bg=COLORS['bg_secondary'],
    fg=COLORS['text_primary'],
    borderwidth=2,
    relief=tk.GROOVE
)
positions_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

# Stats
stats_frame = tk.Frame(positions_frame, bg=COLORS['bg_secondary'])
stats_frame.pack(fill=tk.X, padx=15, pady=10)

tk.Label(
    stats_frame,
    text="Total de posições:",
    font=("Segoe UI", 10),
    bg=COLORS['bg_secondary'],
    fg=COLORS['text_secondary']
).pack(side=tk.LEFT)

positions_count_label = tk.Label(
    stats_frame,
    text="0",
    font=("Segoe UI", 10, "bold"),
    bg=COLORS['bg_secondary'],
    fg=COLORS['accent_blue']
)
positions_count_label.pack(side=tk.LEFT, padx=5)

# Botões de ação
buttons_frame = tk.Frame(positions_frame, bg=COLORS['bg_secondary'])
buttons_frame.pack(fill=tk.X, padx=15, pady=(0, 10))

capture_button = ttk.Button(
    buttons_frame,
    text="➕ Adicionar Posição",
    command=capture_click,
    style="Accent.TButton"
)
capture_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

clear_button = ttk.Button(
    buttons_frame,
    text="🗑️ Limpar Tudo",
    command=clear_positions,
    style="TButton"
)
clear_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

# Lista de posições
list_container = tk.Frame(positions_frame, bg=COLORS['bg_tertiary'])
list_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

scrollbar = tk.Scrollbar(list_container)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

position_listbox = tk.Listbox(
    list_container,
    height=6,
    font=("Consolas", 10),
    bg=COLORS['bg_tertiary'],
    fg=COLORS['text_primary'],
    selectbackground=COLORS['accent_blue'],
    selectforeground=COLORS['bg_primary'],
    borderwidth=0,
    highlightthickness=0,
    yscrollcommand=scrollbar.set
)
position_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
scrollbar.config(command=position_listbox.yview)

remove_button = ttk.Button(
    positions_frame,
    text="➖ Remover Selecionado",
    command=remove_position,
    style="TButton"
)
remove_button.pack(pady=(0, 15), padx=15)

# -----------------------------------------------------------------------------
# SEÇÃO: CONFIGURAÇÕES
# -----------------------------------------------------------------------------
settings_frame = tk.LabelFrame(
    main_container,
    text="  ⚙️ CONFIGURAÇÕES  ",
    font=("Segoe UI", 11, "bold"),
    bg=COLORS['bg_secondary'],
    fg=COLORS['text_primary'],
    borderwidth=2,
    relief=tk.GROOVE
)
settings_frame.pack(fill=tk.X, pady=(0, 10))

settings_container = tk.Frame(settings_frame, bg=COLORS['bg_secondary'])
settings_container.pack(pady=15, padx=15, fill=tk.X)

# Coluna esquerda
left_settings = tk.Frame(settings_container, bg=COLORS['bg_secondary'])
left_settings.pack(side=tk.LEFT, fill=tk.X, expand=True)

def create_checkbox(parent, text, variable):
    cb_frame = tk.Frame(parent, bg=COLORS['bg_secondary'])
    cb_frame.pack(anchor="w", pady=5)
    
    cb = tk.Checkbutton(
        cb_frame,
        text=text,
        variable=variable,
        font=("Segoe UI", 10),
        bg=COLORS['bg_secondary'],
        fg=COLORS['text_primary'],
        selectcolor=COLORS['bg_tertiary'],
        activebackground=COLORS['bg_secondary'],
        activeforeground=COLORS['accent_blue'],
        borderwidth=0,
        highlightthickness=0
    )
    cb.pack(anchor="w")

create_checkbox(left_settings, "🍖  Comer automaticamente", auto_eat_enabled)
create_checkbox(left_settings, "⚔️  Atacar automaticamente", auto_attack_enabled)
create_checkbox(left_settings, "✨  Detectar shiny", auto_shiny_enabled)
create_checkbox(left_settings, "💎  Loot automático", auto_loot_enabled)

# Coluna direita - Configuração de teclas
right_settings = tk.Frame(settings_container, bg=COLORS['bg_secondary'])
right_settings.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(20, 0))

tk.Label(
    right_settings,
    text="Teclas Personalizadas:",
    font=("Segoe UI", 9, "bold"),
    bg=COLORS['bg_secondary'],
    fg=COLORS['text_secondary']
).pack(anchor="w", pady=(0, 5))

# Campo para tecla de pesca
fishing_key_frame = tk.Frame(right_settings, bg=COLORS['bg_secondary'])
fishing_key_frame.pack(anchor="w", pady=3, fill=tk.X)

tk.Label(
    fishing_key_frame,
    text="Pesca:",
    font=("Segoe UI", 9),
    bg=COLORS['bg_secondary'],
    fg=COLORS['text_primary'],
    width=10,
    anchor="w"
).pack(side=tk.LEFT)

fishing_key_entry = tk.Entry(
    fishing_key_frame,
    font=("Consolas", 9),
    bg=COLORS['bg_tertiary'],
    fg=COLORS['text_primary'],
    insertbackground=COLORS['text_primary'],
    borderwidth=1,
    relief=tk.SOLID,
    width=15
)
fishing_key_entry.pack(side=tk.LEFT, padx=5)
fishing_key_entry.insert(0, DEFAULT_FISHING_KEY)

# Campo para tecla de selecionar alvo
target_key_frame = tk.Frame(right_settings, bg=COLORS['bg_secondary'])
target_key_frame.pack(anchor="w", pady=3, fill=tk.X)

tk.Label(
    target_key_frame,
    text="Sel. Alvo:",
    font=("Segoe UI", 9),
    bg=COLORS['bg_secondary'],
    fg=COLORS['text_primary'],
    width=10,
    anchor="w"
).pack(side=tk.LEFT)

target_key_entry = tk.Entry(
    target_key_frame,
    font=("Consolas", 9),
    bg=COLORS['bg_tertiary'],
    fg=COLORS['text_primary'],
    insertbackground=COLORS['text_primary'],
    borderwidth=1,
    relief=tk.SOLID,
    width=15
)
target_key_entry.pack(side=tk.LEFT, padx=5)
target_key_entry.insert(0, DEFAULT_TARGET_KEY)

# Campo para tecla de loot
loot_frame = tk.Frame(right_settings, bg=COLORS['bg_secondary'])
loot_frame.pack(anchor="w", pady=3, fill=tk.X)

tk.Label(
    loot_frame,
    text="Loot:",
    font=("Segoe UI", 9),
    bg=COLORS['bg_secondary'],
    fg=COLORS['text_primary'],
    width=10,
    anchor="w"
).pack(side=tk.LEFT)

loot_key_entry = tk.Entry(
    loot_frame,
    font=("Consolas", 9),
    bg=COLORS['bg_tertiary'],
    fg=COLORS['text_primary'],
    insertbackground=COLORS['text_primary'],
    borderwidth=1,
    relief=tk.SOLID,
    width=15
)
loot_key_entry.pack(side=tk.LEFT, padx=5)
loot_key_entry.insert(0, DEFAULT_LOOT_KEY)

# Campo para tecla de parar pokémon
stop_frame = tk.Frame(right_settings, bg=COLORS['bg_secondary'])
stop_frame.pack(anchor="w", pady=3, fill=tk.X)

tk.Label(
    stop_frame,
    text="Parar Pkmn:",
    font=("Segoe UI", 9),
    bg=COLORS['bg_secondary'],
    fg=COLORS['text_primary'],
    width=10,
    anchor="w"
).pack(side=tk.LEFT)

stop_pokemon_key_entry = tk.Entry(
    stop_frame,
    font=("Consolas", 9),
    bg=COLORS['bg_tertiary'],
    fg=COLORS['text_primary'],
    insertbackground=COLORS['text_primary'],
    borderwidth=1,
    relief=tk.SOLID,
    width=15
)
stop_pokemon_key_entry.pack(side=tk.LEFT, padx=5)
stop_pokemon_key_entry.insert(0, DEFAULT_STOP_POKEMON_KEY)

# -----------------------------------------------------------------------------
# SEÇÃO: ATAQUES
# -----------------------------------------------------------------------------
attacks_frame = tk.LabelFrame(
    main_container,
    text="  ⚔️ SELEÇÃO DE ATAQUES  ",
    font=("Segoe UI", 11, "bold"),
    bg=COLORS['bg_secondary'],
    fg=COLORS['text_primary'],
    borderwidth=2,
    relief=tk.GROOVE
)
attacks_frame.pack(fill=tk.X, pady=(0, 10))

attacks_container = tk.Frame(attacks_frame, bg=COLORS['bg_secondary'])
attacks_container.pack(pady=15, padx=15)

for i, (key, var) in enumerate(attack_keys.items()):
    cb = tk.Checkbutton(
        attacks_container,
        text=key,
        variable=var,
        font=("Segoe UI", 9, "bold"),
        bg=COLORS['bg_secondary'],
        fg=COLORS['text_primary'],
        selectcolor=COLORS['bg_tertiary'],
        activebackground=COLORS['bg_secondary'],
        activeforeground=COLORS['accent_green'],
        borderwidth=0,
        highlightthickness=0,
        width=5
    )
    cb.pack(side=tk.LEFT, padx=3)

# -----------------------------------------------------------------------------
# SEÇÃO: LOGS
# -----------------------------------------------------------------------------
log_frame = tk.LabelFrame(
    main_container,
    text="  📋 LOGS  ",
    font=("Segoe UI", 11, "bold"),
    bg=COLORS['bg_secondary'],
    fg=COLORS['text_primary'],
    borderwidth=2,
    relief=tk.GROOVE
)
log_frame.pack(fill=tk.BOTH, expand=True)

log_box = scrolledtext.ScrolledText(
    log_frame,
    height=12,
    font=("Consolas", 9),
    bg=COLORS['bg_tertiary'],
    fg=COLORS['text_primary'],
    insertbackground=COLORS['text_primary'],
    borderwidth=0,
    highlightthickness=0,
    wrap=tk.WORD,
    state=tk.DISABLED
)
log_box.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

# Configurar tags de cores para logs
log_box.tag_config("info", foreground=COLORS['accent_blue'])
log_box.tag_config("success", foreground=COLORS['success'])
log_box.tag_config("warning", foreground=COLORS['warning'])
log_box.tag_config("error", foreground=COLORS['error'])

# =============================================================================
# FOOTER
# =============================================================================
footer_frame = tk.Frame(window, bg=COLORS['bg_secondary'], height=40)
footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
footer_frame.pack_propagate(False)

footer_label = tk.Label(
    footer_frame,
    text="Desenvolvido com ❤️ | Versão 2.0",
    font=("Segoe UI", 9),
    bg=COLORS['bg_secondary'],
    fg=COLORS['text_secondary']
)
footer_label.pack(pady=10)

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
log("═" * 60, "info")
log("🎣 FISHING BOT PRO INICIADO v2.2", "success")
log("⌨️  Tecla H: Ligar/Desligar bot", "info")
log("📍 Adicione posições de pesca para começar", "info")
log(f"🔄 O bot para a cada {LOOPS_BEFORE_STOP} loops para descanso", "info")
log("🎯 TAB seleciona alvo → Tecla de ataque real (padrão: 1)", "info")
log("💎 Loot automático ativado por padrão", "info")
log("═" * 60, "info")

# Atualizar estatísticas iniciais
update_stats()

# Resetar botão de captura caso esteja em estado incorreto
capture_button.config(text="➕ Adicionar Posição", style="Accent.TButton")

# Iniciar aplicação
window.mainloop()
