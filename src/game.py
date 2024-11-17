import time
import uuid
import setup_game
import math
from pynput import keyboard
from setup_game import create_screen, create_turtle

ATUALIZATIONS_PER_SECOND = 100
DELAY = 1.0 / ATUALIZATIONS_PER_SECOND
TURTLE_STEP_PER_SECOND = 200

turtle_by_id = {}  # Relaciona IDs de jogadores com as tartarugas
initial_info_by_id = {}  # Relaciona IDs de jogadores com as informações iniciais (cor, posição inicial)

player_id = str(uuid.uuid4())
player_turtle = None
is_game_running = True


def on_publish(client, userdata, result):
    pass

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    if rc == 0:
        print("Conexão bem-sucedida!")
    else:
        print("Falha na conexão. Código de erro:", rc)
    client.subscribe("/data")


def on_message(client, userdata, msg):
    data = msg.payload.decode().split(":")
    # Mensagem de conexão: "CONNECT:UUID:turtleColor:x,y"
    if data[0] == "CONNECT" and len(data) == 4:  # Registrar informações iniciais do jogador
        received_id = data[1]
        if received_id == player_id:
            return

        turtle_color = data[2]
        initial_pos = tuple(map(float, data[3].strip("()").split(",")))

        # Criar uma nova turtle se ela ainda não existir
        if received_id not in turtle_by_id:
            initial_info_by_id[received_id] = {'color': turtle_color, 'initial_pos': initial_pos}
            print(f"Novo jogador {received_id} conectado com cor {turtle_color} e posição inicial {initial_pos}.")

        connect_message()

    # Mensagem de movimentação: "UUID:(x,y)"
    elif len(data) == 2:  # Receber posição do player
        received_id = data[0]
        if received_id == player_id:
            return

        if received_id not in turtle_by_id:
            print(f"Jogador {received_id} não está conectado. Ignorando movimentação.")
            return

        position_data = data[1].strip("()").split(",")
        if len(position_data) != 2:
            print("Erro: Coordenadas recebidas em formato inesperado:", data[1])
            return

        try:
            position = tuple(map(float, position_data))
            turtle = turtle_by_id[received_id]
        except ValueError as e:
            print("Erro ao converter coordenadas para float:", e)
            return

        turtle.current_position = position
        turtle.changed_position = True

def connect_message():
    color = player_turtle.choosedColor
    initial_pos = player_turtle.position()  # Obtém a posição inicial do jogador
    publisher.publish("/data", f"CONNECT:{player_id}:{color}:{initial_pos}")
    print(f"Mensagem de conexão enviada do player {player_id} da cor {color} e posição inicial {initial_pos}")


def update_current_player_coordinate(delta_time):
    dx = dy = 0
    turtle_step = TURTLE_STEP_PER_SECOND * delta_time

    if directions_pressed['up']:
        dy += turtle_step
    if directions_pressed['down']:
        dy -= turtle_step
    if directions_pressed['left']:
        dx -= turtle_step
    if directions_pressed['right']:
        dx += turtle_step

    # Normaliza a velocidade ao mover na diagonal
    if dx != 0 and dy != 0:
        dx = (1 if dx > 0 else -1) * turtle_step / math.sqrt(2)
        dy = (1 if dy > 0 else -1) * turtle_step / math.sqrt(2)

    # Atualiza a direção do player no dicionário turtle_by_id
    player_turtle.current_position = (player_turtle.xcor() + dx, player_turtle.ycor() + dy)
    player_turtle.changed_position = True


def publish_move():
    is_moving = any(directions_pressed.values()) and not (
            directions_pressed.get("right") and directions_pressed.get("left") or
            directions_pressed.get("up") and directions_pressed.get("down")
    )

    if is_moving:
        publisher.publish("/data", f"{player_id}:{player_turtle.position()}")


def move_turtles(delta_time):
    update_current_player_coordinate(delta_time)

    # Iterar sobre tartarugas já inicializadas
    for registered_player_id, info in initial_info_by_id.copy().items():
        # Criar nova tartaruga caso não instanciada
        if registered_player_id not in turtle_by_id:
            new_turtle = create_turtle(info['color'])
            new_turtle.changed_position = True
            new_turtle.current_position = info['initial_pos']  # Usar a posição inicial do jogador
            turtle_by_id[registered_player_id] = new_turtle

        # Atualiza a posição da tartaruga
        turtle = turtle_by_id[registered_player_id]
        if turtle.changed_position:
            turtle.goto(turtle.current_position)
            turtle.changed_position = False

    window.update()

def game_loop(last_time):
    if not is_game_running:
        return

    current_time = time.time()
    delta_time = current_time - last_time
    move_turtles(delta_time)
    publish_move()

    # Reagendar o loop com o novo last_time
    window.ontimer(lambda: game_loop(current_time), int(DELAY * 1000))

def on_press(key):
    set_direction_state(key, True)

def on_release(key):
    set_direction_state(key, False)

def set_direction_state(key, state):
    if not hasattr(key, 'char'):
        return
    char = key.char.lower()
    if char not in mappings:
        return
    directions_pressed[mappings[char]] = state

def on_escape():
    global is_game_running
    is_game_running = False
    window.bye()
    if listener:
        listener.stop()


if __name__ == "__main__":
    window = create_screen()

    player_turtle = create_turtle()
    player_turtle.changed_position = True
    player_turtle.current_position = player_turtle.position()  # Usar a posição inicial do jogador
    turtle_by_id[player_id] = player_turtle
    initial_info_by_id[player_id] = {'color': player_turtle.choosedColor, 'initial_pos': player_turtle.position()}

    publisher = setup_game.create_publisher(on_publish)
    data_receiver = setup_game.create_data_receiver(on_connect, on_message)

    window.listen()
    window.onkey(on_escape, "Escape")

    mappings = setup_game.read_directions()
    print("Teclas mapeadas: ", mappings)

    connect_message()

    directions_pressed = {'up': False, 'down': False, 'left': False, 'right': False}

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()

    game_loop(time.time())
    window.mainloop()
