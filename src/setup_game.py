import turtle
import paho.mqtt.client as mqtt_client
from tkinter.colorchooser import askcolor

# Configurações MQTT
BROKER_IP = "localhost"
BROKER_PORT = 1883
KEEPALIVE = 60

# Função para abrir o seletor de cor
def choose_color(prompt="Escolha uma cor"):
    color = askcolor(title=prompt)
    if color[1] is not None:
        return color[1]  # Retorna a cor em formato hexadecimal
    return ""


# Função para criar a tela (Screen)
def create_screen():
    window = turtle.Screen()
    window.title("Move Game by @Luiz")
    window.setup(width=800, height=600)
    fundo_cor = choose_color("Escolha a cor de fundo")
    if fundo_cor != "":
        window.bgcolor(fundo_cor)
    return window


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
    publisher = mqtt_client.Client()

    publisher.on_publish = on_publish
    publisher.connect(BROKER_IP, BROKER_PORT)

    return publisher


# Função para criar o data_receiver e configurar os callbacks on_connect e on_message
def create_data_receiver(on_connect, on_message):
    data_receiver = mqtt_client.Client()
    data_receiver.on_connect = on_connect
    data_receiver.on_message = on_message
    data_receiver.connect(BROKER_IP, BROKER_PORT, KEEPALIVE)
    data_receiver.loop_start()

    return data_receiver


from tkinter import Tk, Label

def read_directions():
    directions_sequence = ['up', 'down', 'left', 'right']
    directions_map = {}  # Chave: tecla, valor: direção

    root = Tk()
    root.title("Mapeamento de Teclas")
    root.geometry("400x300")

    label_text = "Pressione as teclas para mapear as direções.\nPressione qualquer tecla para começar"
    label = Label(root, text=label_text, font=("Arial", 12))
    label.pack(pady=20)

    current_direction_index = 0
    waiting_start = True

    def on_key_press(event):
        nonlocal waiting_start, current_direction_index
        if waiting_start:
            waiting_start = False
            update_label()
        elif event.char and event.char.lower() not in directions_map.keys():
            directions_map[event.char.lower()] = directions_sequence[current_direction_index]
            label.config(text=f"{directions_sequence[current_direction_index].capitalize()}: {event.char}")

            current_direction_index += 1
            if current_direction_index < len(directions_sequence):
                root.after(500, update_label)  # Avança para a próxima direção após 0.5s
            else:
                root.quit()  # Encerra após o último mapeamento

    update_label = lambda: label.config(text=f"{directions_sequence[current_direction_index].capitalize()}: ___")

    root.bind("<KeyPress>", on_key_press)
    root.mainloop()
    root.destroy()

    return directions_map