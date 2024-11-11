import threading
import time
import uuid
import setup_game
import math
from pynput import keyboard
from setup_game import create_screen, create_turtle  # Importando as funções

ATUALIZATIONS_PER_SECOND = 100
DELAY = 1.0 / ATUALIZATIONS_PER_SECOND
TURTLE_STEP_PER_SECOND = 200

# Dicionário que relaciona UUIDs com suas respectivas turtles
players = {}

# ID único para este jogador
player_id = str(uuid.uuid4())

# Flag para verificar se o jogador foi conectado
connected = False

# Configurando PUBLISHER
def on_publish(client, userdata, result):
    pass


# Configurando DATA_RECEIVER
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("/data")

# Configurando DATA_RECEIVER
def on_message(client, userdata, msg):
    try:
        # Decodifica o payload e divide pelo delimitador ":"
        data = msg.payload.decode().split(":")

        # Verifica se a mensagem é de conexão ou de movimentação
        if data[0] == "CONNECT" and len(data) == 3:
            # Mensagem de conexão: "CONNECT:UUID:turtleColor"
            received_id = data[1]
            turtle_color = data[2]

            # Cria uma nova turtle para o jogador e define sua cor
            if received_id not in players:
                new_turtle = create_turtle(turtle_color)
                players[received_id] = new_turtle
                print(f"Novo jogador {received_id} conectado com cor {turtle_color}.")

                # Envia uma mensagem de conexão própria para o novo jogador
                if received_id != player_id:
                    connect_message()
            else:
                print(f"Jogador {received_id} já está conectado.")

        elif len(data) == 2:
            # Mensagem de movimentação: "UUID:(x,y)"
            received_id = data[0]

            # Verifica se o jogador já foi registrado (recebeu mensagem de conexão)
            if received_id not in players:
                print(f"Jogador {received_id} não está conectado. Ignorando movimentação.")
                return

            # Extrai e converte as coordenadas para float
            position_data = data[1].strip("()").split(",")
            if len(position_data) != 2:
                print("Erro: Coordenadas recebidas em formato inesperado:", data[1])
                return

            # Converte as coordenadas para float
            position = tuple(map(float, position_data))

            # Atualiza a posição da turtle do jogador no dicionário
            turtle = players[received_id]
            threading.Thread(target=turtle.goto, args=(position[0], position[1])).start()
            # print(f"Jogador {received_id} movido para {position}")

    except ValueError as e:
        print("Erro ao converter coordenadas para float:", e)

def connect_message():
    global connected
    color = player_turtle.choosedColor  # Utiliza a cor diretamente do atributo 'choosedColor'
    publisher.publish("/data", f"CONNECT:{player_id}:{color}")
    connected = True
    print(f"Mensagem de conexão enviada do player {player_id} da cor {color}")

def manage_direction(delta_time):
    if not connected:
        return

    dx = dy = 0
    turtle_step = TURTLE_STEP_PER_SECOND * delta_time  # Movimentação ajustada pelo deltaTime

    # Define o movimento com base nas direções pressionadas
    if directions_pressed['up']:
        dy += turtle_step
    if directions_pressed['down']:
        dy -= turtle_step
    if directions_pressed['left']:
        dx -= turtle_step
    if directions_pressed['right']:
        dx += turtle_step

    # Compensa o movimento diagonal
    if dx != 0 and dy != 0:
        dx = (1 if dx > 0 else -1) * turtle_step / math.sqrt(2)
        dy = (1 if dy > 0 else -1) * turtle_step / math.sqrt(2)

    # Move a tartaruga deste jogador
    players[player_id].setx(players[player_id].xcor() + dx)
    players[player_id].sety(players[player_id].ycor() + dy)


def synchronize():
    if not connected:
        return

    is_moving = any(directions_pressed.values()) and not (
            directions_pressed.get("right") and directions_pressed.get("left") or
            directions_pressed.get("up") and directions_pressed.get("down")
    )

    if is_moving:
        # Envia o UUID e a posição atual do jogador para o tópico MQTT
        publisher.publish("/data", f"{player_id}:{players[player_id].position()}")


def move():
    global last_time
    current_time = time.time()
    delta_time = current_time - last_time  # Calculando o deltaTime
    last_time = current_time  # Atualiza o tempo para a próxima iteração
    manage_direction(delta_time)
    wn.update()


def game_loop():
    move()
    synchronize()
    wn.ontimer(game_loop, int(DELAY * 1000))  # Chama o game_loop novamente após o delay


# Gerencia teclada pressionada
def on_press(key):
    try:
        if key == keyboard.KeyCode.from_char(mappings['up']):
            directions_pressed['up'] = True
        elif key == keyboard.KeyCode.from_char(mappings['left']):
            directions_pressed['left'] = True
        elif key == keyboard.KeyCode.from_char(mappings['down']):
            directions_pressed['down'] = True
        elif key == keyboard.KeyCode.from_char(mappings['right']):
            directions_pressed['right'] = True
    except AttributeError:
        pass  # Caso o evento seja uma tecla especial (como shift, ctrl)


# Gerencia tecla liberada
def on_release(key):
    try:
        if key == keyboard.KeyCode.from_char(mappings['up']):
            directions_pressed['up'] = False
        elif key == keyboard.KeyCode.from_char(mappings['left']):
            directions_pressed['left'] = False
        elif key == keyboard.KeyCode.from_char(mappings['down']):
            directions_pressed['down'] = False
        elif key == keyboard.KeyCode.from_char(mappings['right']):
            directions_pressed['right'] = False
    except AttributeError:
        pass  # Caso o evento seja uma tecla especial (como shift, ctrl)


def on_escape():
    wn.bye()
    if listener:
        listener.stop()


if __name__ == "__main__":
    wn = create_screen()

    # Cria a turtle para este jogador e adiciona ao dicionário de players
    player_turtle = create_turtle()  # Ou escolha uma cor
    players[player_id] = player_turtle

    # Agora que a tartaruga foi criada, podemos criar o publisher e o data_receiver
    publisher = setup_game.create_publisher(on_publish)
    data_receiver = setup_game.create_data_receiver(on_connect, on_message)

    wn.listen()
    wn.onkey(on_escape, "Escape")

    mappings = setup_game.read_directions()  # Lê os mapeamentos de teclas
    print("Teclas mapeadas: ", mappings)

    connect_message()

    directions_pressed = {'up': False, 'down': False, 'left': False, 'right': False}

    # Variável para controlar o deltaTime
    last_time = time.time()

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()  # Inicia o listener em segundo plano

    game_loop()
    wn.mainloop()