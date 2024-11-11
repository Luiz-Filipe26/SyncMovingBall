import turtle
import paho.mqtt.client as mqttClient
import paho.mqtt as mqtt
from tkinter import Tk, Label
from tkinter.colorchooser import askcolor
import time

# Configurações MQTT
BROKER_IP = "localhost"
BROKER_PORT = 1883
KEEPALIVE = 60

# Função para abrir o seletor de cor
def choose_color(prompt="Escolha uma cor"):
    color = askcolor(title=prompt)
    if color[1] is not None:
        return color[1]  # Retorna a cor em formato hexadecimal
    return None


# Função para criar a tela (Screen)
def create_screen():
    wn = turtle.Screen()
    wn.title("Move Game by @Luiz")
    wn.setup(width=800, height=600)
    fundo_cor = choose_color("Escolha a cor de fundo")
    if fundo_cor:
        wn.bgcolor(fundo_cor)
    return wn


# Função para criar a tartaruga (Turtle) e aplicar a cor
def create_turtle(color=None):
    head = turtle.Turtle("circle")
    head.penup()

    tartaruga_cor = color if color else choose_color("Escolha a cor da tartaruga")

    if tartaruga_cor:
        head.color(tartaruga_cor)
        head.choosedColor = tartaruga_cor  # Armazena a cor escolhida em formato hexadecimal

    return head


# Função para criar o publisher e conectar ao broker
def create_publisher(on_publish=None):
    if mqtt.__version__[0] > '1':
        publisher = mqttClient.Client(mqttClient.CallbackAPIVersion.VERSION1, "admin")
    else:
        publisher = mqttClient.Client()

    publisher.on_publish = on_publish
    publisher.connect(BROKER_IP, BROKER_PORT)

    return publisher


# Função para criar o data_receiver e configurar os callbacks on_connect e on_message
def create_data_receiver(on_connect, on_message):
    data_receiver = mqttClient.Client()
    data_receiver.on_connect = on_connect
    data_receiver.on_message = on_message
    data_receiver.connect(BROKER_IP, BROKER_PORT, KEEPALIVE)
    data_receiver.loop_start()

    return data_receiver


def read_directions():
    # Dicionário para armazenar o mapeamento das teclas
    directions_map = {'up': None, 'down': None, 'left': None, 'right': None}

    # Cria a tela Tkinter para mostrar o status da configuração
    root = Tk()
    root.title("Mapeamento de Teclas")
    root.geometry("400x300")

    # Label que será atualizado com o mapeamento das teclas
    label = Label(root, text="Pressione as teclas para mapear as direções.\nPressione qualquer tecla para começar", font=("Arial", 12))
    label.pack(pady=20)

    waiting_start = True

    def on_key_press(event):
        nonlocal waiting_start
        if waiting_start:
            waiting_start = False
            update_next_direction()
        elif event.char and event.char not in directions_map.values():
            if directions_map['up'] is None:
                directions_map['up'] = event.char
                label.config(text=f"Up: {event.char}")
                root.after(500, update_next_direction)  # Aguarda 0.5s para passar para o próximo
            elif directions_map['down'] is None:
                directions_map['down'] = event.char
                label.config(text=f"Down: {event.char}")
                root.after(500, update_next_direction)
            elif directions_map['left'] is None:
                directions_map['left'] = event.char
                label.config(text=f"Left: {event.char}")
                root.after(500, update_next_direction)
            elif directions_map['right'] is None:
                directions_map['right'] = event.char
                label.config(text=f"Right: {event.char}")
                root.quit()  # Finaliza após o último mapeamento

    # Função que avança para a próxima direção
    def update_next_direction():
        # Atualiza o texto do Label para o próximo mapeamento
        if directions_map['up'] is None:
            label.config(text="Up: ___")
        if directions_map['up'] is not None and directions_map['down'] is None:
            label.config(text="Down: ___")
        elif directions_map['down'] is not None and directions_map['left'] is None:
            label.config(text="Left: ___")
        elif directions_map['left'] is not None and directions_map['right'] is None:
            label.config(text="Right: ___")

    # Vincula a captura de teclas à função de mapeamento
    root.bind("<KeyPress>", on_key_press)

    # Inicia o loop principal do tkinter para escutar os eventos de teclado
    root.mainloop()  # O loop mantém a janela ativa até o mapeamento ser completado

    root.quit()  # Garante que o tkinter termine adequadamente
    root.destroy()  # Encerra o tkinter

    return directions_map