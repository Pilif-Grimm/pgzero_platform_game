import pgzrun

# Constantes:
TILE_SIZE = 64
ROWS = 15
COLS = 20

WIDTH = TILE_SIZE * COLS
HEIGHT = TILE_SIZE * ROWS
TITLE = "Jogo de Plataforma"

JUMP_FORCE = -14.2

ANIMATION_SPEED_WALK = 0.14
ANIMATION_SPEED_IDLE = 0.4

# Config Menu
estado = "menu"
botao_largura = 250
botao_altura = 60
botao_x = (WIDTH - botao_largura) // 2  # centraliza horizontalmente
# Criando botões
botao_comecar = Rect((botao_x, 150), (botao_largura, botao_altura))
botao_musica = Rect((botao_x, 250), (botao_largura, botao_altura))
botao_sons = Rect((botao_x, 350), (botao_largura, botao_altura))
botao_sair = Rect((botao_x, 450), (botao_largura, botao_altura))
# Variáveis de toggle
musica_ligada = True
if musica_ligada:
    music.play("background")
sounds_on = True
# Cor padrão dos botões
cor_padrao = {"comecar": "blue", "musica": "green", "sons": "orange", "sair": "red"}
# Cor de hover
cor_hover = "yellow"
mouse_pos_atual = (0, 0)



# Classes dos personagens
# Classe pai para as animações
class AnimatedEntity(Actor):
    def __init__(self, frames, pos, animation_speed=0.5):
        super().__init__(frames[0], pos)

        self.frames = frames
        self.frame_index = 0
        self.animation_speed = animation_speed
        self.frame_timer = 0

    def set_state(self, new_state):
        if new_state != self.state:

            old_bottom = self.bottom

            self.state = new_state
            self.frames = self.animations[self.state]
            self.frame_index = 0
            self.frame_timer = 0
            self.image = self.frames[0]

            # velocidade por estado
            if self.state in ("walkright", "walkleft"):
                self.animation_speed = ANIMATION_SPEED_WALK
            else:
                self.animation_speed = ANIMATION_SPEED_IDLE

            self.bottom = old_bottom
    
    
    def update_animation(self, dt):
        self.frame_timer += dt

        if self.frame_timer >= self.animation_speed:
            self.frame_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.image = self.frames[self.frame_index]

# Classe para o heroi, herda da classe animação mas adiciona
# movimento do heroi a partir de input, gravidade e colisões.
class Hero(AnimatedEntity):
    def __init__(self, x, y, gravity=0.5):

        self.animations = {
            "idle": ["hero_idle_0", "hero_idle_1", "hero_idle_2", "hero_idle_3"],
            "walkleft": ["hero_walkleft_0", "hero_walkleft_1"],
            "walkright": ["hero_walkright_0", "hero_walkright_1"],
            "jump": ["hero_jump"]
        }

        self.state = "idle"

        super().__init__(self.animations[self.state], (x, y), animation_speed=0.4)

        self.vel_x = 0
        self.vel_y = 0
        self.gravity = gravity
        self.speed = 4
        self.jump_force = JUMP_FORCE
        self.on_ground = False

    def handle_input(self):
        if keyboard.left:
            self.vel_x = -self.speed
        elif keyboard.right:
            self.vel_x = self.speed
        else:
            self.vel_x = 0

        if keyboard.up and self.on_ground:
            self.vel_y = self.jump_force
            self.on_ground = False
            if sounds_on:
                    sounds.sfx_jump.play()
    
    def move(self, platforms):
        # Gravidade
        self.vel_y += self.gravity

        # Movimento horizontal
        self.x += self.vel_x
        self.resolve_collision_x(platforms)

        # Movimento vertical
        self.y += self.vel_y
        self.resolve_collision_y(platforms)

    def resolve_collision_y(self, platforms):
        self.on_ground = False

        for platform in platforms:
            if self.colliderect(platform):

                # Caindo
                if self.vel_y >= 0:
                    self.bottom = platform.top
                    self.vel_y = 0
                    self.on_ground = True

                # Subindo (batendo a cabeça)
                elif self.vel_y < 0:
                    self.top = platform.bottom
                    self.vel_y = 0

    def resolve_collision_x(self, platforms):
        for platform in platforms:
            if self.colliderect(platform):

                # Indo para a direita
                if self.vel_x > 0:
                    self.right = platform.left
                    self.vel_x = 0

                # Indo para a esquerda
                elif self.vel_x < 0:
                    self.left = platform.right
                    self.vel_x = 0


    def update(self, dt, platforms):

        self.handle_input()
        self.move(platforms)

        if not self.on_ground:
            self.set_state("jump")
        elif self.vel_x > 0:
            self.set_state("walkright")
        elif self.vel_x < 0:
            self.set_state("walkleft")
        else:
            self.set_state("idle")

        self.update_animation(dt)

        # Estou usando a variavel global, no futuro posso usar como parametro
        for obstacle in obstacles:
            if self.colliderect(obstacle):
                return True
        for enemy in enemies:
            if self.colliderect(enemy):
                return True
        if saw1.active and hero.colliderect(saw1):
            return True
        # Se a bandeira estiver ativa e o heroi toca-la, será vitória
        # Por enquanto vou deixar o mesmo efeito de morte
        if flag.active and hero.colliderect(flag):
            if sounds_on:
                    sounds.sfx_magic.play()
            return True
        return False

# Classe para os inimigos que se movem, herda da classe animação "AnimatedEntity"
class Enemy(AnimatedEntity):
    def __init__(self, x, y, name, speed=2, left_limit=0, patrol_distance=200, direction=1):

        # Sprites
        walkright_frames = [f"{name}_walkright_0", f"{name}_walkright_1"]
        walkleft_frames  = [f"{name}_walkleft_0",  f"{name}_walkleft_1"]

        self.animations = {"walkright": walkright_frames, "walkleft": walkleft_frames}

        # Estado inicial
        self.direction = direction
        self.state = "walkright" if direction > 0 else "walkleft"

        # Inicializa sprite
        super().__init__(self.animations[self.state], (x, y), animation_speed=0.2)

        # Alinhamento por borda e base
        self.bottom = y

        # Limites da patrulha
        self.left_limit = left_limit
        self.right_limit = left_limit + patrol_distance

        # Força posição inicial dentro da faixa
        self.left = max(min(x, self.right_limit), self.left_limit)

        # Velocidade
        self.speed = speed

    def move(self):
        # Movimenta
        self.left += self.speed * self.direction

        # Inverte direção ao atingir limites
        if self.left <= self.left_limit:
            self.left = self.left_limit
            self.direction = 1
            self.set_state("walkright")
        elif self.left >= self.right_limit:
            self.left = self.right_limit
            self.direction = -1
            self.set_state("walkleft")

    def update(self, dt):
        self.move()
        self.update_animation(dt)

class EnemySaw(AnimatedEntity):
    def __init__(self, pos, name, active=True, animation_speed=0.2):
        # Sprites
        attack_frames = [f"{name}_attack_0", f"{name}_attack_1"]
        rest_frame = [f"{name}_rest"]

        super().__init__(attack_frames, (0, 0), animation_speed)  # inicializa temporariamente

        self.animations = {
            "attack": attack_frames,
            "rest": rest_frame
        }

        self.active = active

        # Ajusta posição para alinhar base e esquerda no tile
        self.left, self.bottom = pos

        # Estado inicial
        if not self.active:
            self.set_state("rest")
        else:
            self.state = "attack"

    def update(self, dt):
        if self.active:
            self.update_animation(dt)

class Switch(Actor):
    def __init__(self, name, pos):

        default_image = name
        pressed_image = f"{name}_pressed"
        super().__init__(default_image)

        self.default_image = default_image
        self.pressed_image = pressed_image
        self.left, self.bottom = pos 
        self.pressed = False

    def update(self, hero_actor=None):
 
        if hero_actor and self.colliderect(hero_actor) and not self.pressed:
            self.pressed = True
            self.image = self.pressed_image
            if sounds_on:
                sounds.sfx_gem.play()
            return True
        else:
            if not self.pressed:
                self.image = self.default_image
            return None

class Goal(AnimatedEntity):
    def __init__(self, pos, name, active=False, animation_speed=0.2):
        # Sprites
        active_frames = [f"{name}_0", f"{name}_1"]
        idle_frame = [f"{name}_idle"]

        # Inicializa temporariamente com qualquer frame
        super().__init__(active_frames, (0, 0), animation_speed)

        self.animations = {
            "active": active_frames,
            "idle": idle_frame
        }

        self.active = active

        # Posicionamento correto: alinhar a base e esquerda ao tile
        self.left, self.bottom = pos

        # Estado inicial
        if not self.active:
            self.state = "idle"
            self.set_state("idle")
        else:
            self.state = "active"
            self.set_state("active")

    def update(self, dt):
        if self.active:
            self.update_animation(dt)
        else:
            self.image = self.animations["idle"][0]  # sempre mostra sprite idle

def reset_game():
    global hero
    global enemies
    global switch_red
    global switch_yellow
    global saw1
    global flag

    hero = Hero(TILE_SIZE, HEIGHT - (3*TILE_SIZE))
    
    enemies = [
        Enemy(TILE_SIZE*7, TILE_SIZE*8, "slimefire", speed=2, left_limit = TILE_SIZE*7, patrol_distance = TILE_SIZE*5),
        Enemy(TILE_SIZE*3, TILE_SIZE*4, "slimefire", speed=2, left_limit = TILE_SIZE*3, patrol_distance = TILE_SIZE*4),
        Enemy(TILE_SIZE*1, TILE_SIZE*6, "fly", speed=3, left_limit = 0, patrol_distance = WIDTH),
        Enemy(TILE_SIZE*2, TILE_SIZE*6, "fly", speed=3.2, left_limit = 0, patrol_distance = WIDTH),
        Enemy(TILE_SIZE*4, TILE_SIZE*6, "fly", speed=3.4, left_limit = 0, patrol_distance = WIDTH),
        Enemy(TILE_SIZE*6, TILE_SIZE*6, "fly", speed=4, left_limit = 0, patrol_distance = WIDTH)
    ]
    # Criando switches
    switch_yellow = Switch("switch_yellow", pos=(10*TILE_SIZE, 13*TILE_SIZE))
    switch_red = Switch("switch_red",    pos=(19*TILE_SIZE, 5*TILE_SIZE))
    saw1 = EnemySaw(pos=(1*TILE_SIZE, 7*TILE_SIZE), name="saw", active=True)
    flag = Goal(pos=(19*TILE_SIZE, 14*TILE_SIZE), name="flag")

reset_game()

# Função de Construção de fase
def build(filename, tile_size):
    # abrir o arquivo como leitura
    with open(filename, "r") as f:
        # extrair conteúdo e quebrar linha
        contents = f.read().splitlines()

    # Quebrando linhas em colunas
    contents = [c.split(",") for c in contents]

    # Convertendo strings numéricas em inteiros
    for row in range(len(contents)):
        for col in range(len(contents[0])):
            val = contents[row][col]
            if val and (val.isdigit() or (val[0] == "-" and val[1:].isdigit())):
                contents[row][col] = int(val)

    # Criando os itens que serão construídos
    items = []

    for row in range(len(contents)):
        for col in range(len(contents[0])):
            tile_num = contents[row][col]
            # Verifica se o espaço não é vazio
            if tile_num != -1:
                item = Actor(f"tiles/{tile_num}")
                item.topleft = (tile_size * col, tile_size * row)
                items.append(item)

    return items

# Lendo os arquivos das plataformas e obstaculos
platforms = build("mapa_platforms.csv", TILE_SIZE)
obstacles = build("mapa_obstacles.csv", TILE_SIZE)

def draw_menu():
    screen.fill("skyblue")
    screen.draw.text("MENU INICIAL", center=(WIDTH//2, 70), fontsize=60, color="white")

    # Botão Começar
    cor = cor_hover if botao_comecar.collidepoint(mouse_pos_atual) else cor_padrao["comecar"]
    screen.draw.filled_rect(botao_comecar, cor)
    screen.draw.text("COMECAR O JOGO", center=botao_comecar.center, fontsize=30, color="white")

    # Botão Música
    cor = cor_hover if botao_musica.collidepoint(mouse_pos_atual) else ("green" if musica_ligada else "gray")
    screen.draw.filled_rect(botao_musica, cor)
    texto_musica = "MUSICA LIGADO" if musica_ligada else "MUSICA DESLIGADO"
    screen.draw.text(texto_musica, center=botao_musica.center, fontsize=30, color="white")

    # Botão Sons
    cor = cor_hover if botao_sons.collidepoint(mouse_pos_atual) else ("orange" if sounds_on else "gray")
    screen.draw.filled_rect(botao_sons, cor)
    texto_sons = "SONS LIGADO" if sounds_on else "SONS DESLIGADO"
    screen.draw.text(texto_sons, center=botao_sons.center, fontsize=30, color="white")

    # Botão Sair
    cor = cor_hover if botao_sair.collidepoint(mouse_pos_atual) else cor_padrao["sair"]
    screen.draw.filled_rect(botao_sair, cor)
    screen.draw.text("SAIDA", center=botao_sair.center, fontsize=30, color="white")

def on_mouse_down(pos):
    global estado, musica_ligada, sounds_on
    if estado == "menu":
        if botao_comecar.collidepoint(pos):
            estado = "game"
        elif botao_musica.collidepoint(pos):
            musica_ligada = not musica_ligada
            if musica_ligada:
                 music.play('background')
            else:
                music.stop()
        elif botao_sons.collidepoint(pos):
            sounds_on = not sounds_on
        elif botao_sair.collidepoint(pos):
            quit()

def on_key_down(key):
    global estado
    if key == keys.ESCAPE:
        estado = "menu"

def on_mouse_move(pos):
    global mouse_pos_atual
    mouse_pos_atual = pos

def draw_game():
    screen.clear()
    screen.fill("skyblue")
    for plataform in platforms:
        plataform.draw()
    for obstacle in obstacles:
        obstacle.draw()
    hero.draw()
    for enemy in enemies:
        enemy.draw()
    switch_red.draw()
    switch_yellow.draw()
    saw1.draw()
    flag.draw()

def draw():
    if estado == "menu":
        draw_menu()
    elif estado == "game":
        draw_game()

def update(dt):
    if estado == "game":
        dead = hero.update(dt, platforms)
        if dead:
            if sounds_on:
                    sounds.sfx_bump.play()
            reset_game()
        for enemy in enemies:
            enemy.update(dt)
        if switch_yellow.update(hero):
            saw1.active = False
        if switch_red.update(hero):
            flag.active = True
        saw1.update(dt)
        flag.update(dt)


pgzrun.go()