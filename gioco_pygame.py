import pygame
import random
import math
import sys

# Inizializzazione di Pygame
pygame.init()

# Dimensioni dello schermo
SCREEN_WIDTH = 1900
SCREEN_HEIGHT = 1000
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# Titolo e icona
pygame.display.set_caption("Space Invaders")
icon = pygame.Surface((32, 32))
icon.fill((0, 0, 0))
pygame.draw.rect(icon, (0, 255, 0), (8, 8, 16, 16))
pygame.display.set_icon(icon)

# Font
font = pygame.font.Font(None, 32)
big_font = pygame.font.Font(None, 64)

# Colori
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)

# Stelle di sfondo
stars = []
for i in range(100):
    x = random.randint(0, SCREEN_WIDTH)
    y = random.randint(0, SCREEN_HEIGHT)
    size = random.randint(1, 3)
    brightness = random.randint(100, 255)
    stars.append([x, y, size, brightness])


# Funzione per creare una superficie con un cerchio luminoso (effetto glow)
def create_glow_surface(radius, color, alpha_gradient=True):
    size = radius * 2
    glow = pygame.Surface((size, size), pygame.SRCALPHA)

    if alpha_gradient:
        for i in range(radius, 0, -1):
            alpha = int(255 * (i / radius))
            current_color = (
                *color[:3],
                min(color[3], alpha) if len(color) > 3 else alpha,
            )
            pygame.draw.circle(glow, current_color, (radius, radius), i)
    else:
        pygame.draw.circle(glow, color, (radius, radius), radius)

    return glow


# Cuore per le vite
def create_heart_surface(size=24):
    heart = pygame.Surface((size, size), pygame.SRCALPHA)

    # Disegna il cuore
    heart_color = (255, 50, 50, 255)  # Rosso

    # Crea la forma del cuore con due cerchi e un triangolo
    radius = size // 4
    center_y = size // 3

    # Due cerchi per la parte superiore del cuore
    pygame.draw.circle(heart, heart_color, (radius, center_y), radius)
    pygame.draw.circle(heart, heart_color, (size - radius, center_y), radius)

    # Triangolo per la parte inferiore del cuore
    points = [(0, center_y), (size // 2, size), (size, center_y)]
    pygame.draw.polygon(heart, heart_color, points)

    # Aggiunge un effetto glow
    glow = create_glow_surface(size // 2, (255, 100, 100, 100))
    heart.blit(glow, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    return heart


# Giocatore
class Player:
    def __init__(self):
        self.width = 64
        self.height = 64
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # Disegno della navicella
        pygame.draw.polygon(self.image, WHITE, [(32, 10), (10, 50), (54, 50)])
        pygame.draw.rect(self.image, BLUE, (22, 40, 20, 15))

        # Effetto glow
        glow = create_glow_surface(40, (0, 100, 255, 100))
        self.image.blit(glow, (-8, -8), special_flags=pygame.BLEND_RGBA_ADD)

        self.x = SCREEN_WIDTH // 2 - self.width // 2
        self.y = SCREEN_HEIGHT - 100
        self.speed = 5
        self.lives = 3

        # Effetto propulsori
        self.thruster_timer = 0
        self.thruster_surfaces = []
        for size in range(5, 20, 5):
            thruster = create_glow_surface(size, (255, 100, 0, 150))
            self.thruster_surfaces.append(thruster)

    def draw(self, surface):
        # Disegna la navicella
        surface.blit(self.image, (self.x, self.y))

        # Disegna i propulsori con animazione
        self.thruster_timer = (self.thruster_timer + 1) % 12
        thruster_index = self.thruster_timer // 4
        thruster = self.thruster_surfaces[thruster_index]
        surface.blit(
            thruster,
            (
                self.x + self.width // 2 - thruster.get_width() // 2,
                self.y + self.height - 10,
            ),
        )

    def move(self, direction):
        if direction == "left":
            self.x = max(0, self.x - self.speed)
        elif direction == "right":
            self.x = min(SCREEN_WIDTH - self.width, self.x + self.speed)

    def get_center(self):
        return (self.x + self.width // 2, self.y + self.height // 2)

    def get_collision_rect(self):
        # Ritorna un rettangolo più piccolo per collisioni più precise
        return pygame.Rect(self.x + 20, self.y + 20, self.width - 40, self.height - 40)


# Proiettile
class Bullet:
    def __init__(self, x, y):
        self.width = 6
        self.height = 20
        self.x = x - self.width // 2
        self.y = y
        self.speed = 10
        self.active = True

        # Effetto glow per il proiettile
        self.glow = create_glow_surface(10, (0, 200, 255, 150))

    def move(self):
        self.y -= self.speed
        if self.y < 0:
            self.active = False

    def draw(self, surface):
        # Disegna l'effetto glow
        surface.blit(self.glow, (self.x - 7, self.y - 7))

        # Disegna il corpo del proiettile
        pygame.draw.rect(
            surface, (0, 255, 255), (self.x, self.y, self.width, self.height)
        )


# Nemico
class Enemy:
    def __init__(self, x, y, enemy_type, level=1):
        self.width = 50
        self.height = 50
        self.x = x
        self.y = y
        self.type = enemy_type  # 0, 1, o 2 per tipi diversi di nemici
        self.level = level
        # Velocità aumenta con il livello
        self.speed = (random.uniform(1.0, 2.0) + (0.2 * enemy_type)) * (
            1 + (level - 1) * 0.1
        )
        self.active = True
        self.health = (enemy_type + 1) * (
            1 + (level - 1) // 5
        )  # La salute aumenta ogni 5 livelli
        self.move_timer = 0
        self.move_delay = max(
            60 - (level * 2), 15
        )  # Diminuisce con l'aumentare del livello, min 15
        self.moving_down = (
            False  # Flag per indicare se il nemico si sta muovendo verso il giocatore
        )

        # Colori diversi in base al tipo
        self.colors = [(255, 0, 0), (255, 100, 0), (255, 200, 0)]
        self.color = self.colors[enemy_type]

        # Creiamo l'immagine del nemico
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # Disegno diverso per ogni tipo
        if enemy_type == 0:  # Base
            pygame.draw.polygon(self.image, self.color, [(25, 10), (10, 40), (40, 40)])
        elif enemy_type == 1:  # Medio
            pygame.draw.polygon(self.image, self.color, [(25, 5), (5, 35), (45, 35)])
            pygame.draw.circle(self.image, WHITE, (25, 20), 5)
        else:  # Difficile
            pygame.draw.polygon(self.image, self.color, [(25, 5), (5, 35), (45, 35)])
            pygame.draw.circle(self.image, WHITE, (25, 20), 8)
            pygame.draw.line(self.image, WHITE, (15, 30), (35, 30), 2)

        # Effetto glow
        glow = create_glow_surface(30, (*self.color, 100))
        self.image.blit(glow, (-5, -5), special_flags=pygame.BLEND_RGBA_ADD)

        # Animazione
        self.animation_frame = 0
        self.animation_speed = 0.1

    def move(self, player_x):
        self.move_timer += 1

        # Decide quando iniziare a muoversi verso il giocatore
        if not self.moving_down and self.move_timer >= self.move_delay:
            # Probabilità basata sul livello di difficoltà che il nemico inizi a muoversi verso il giocatore
            # Ridotta la probabilità che i nemici scendano
            chance = (
                0.003 + (0.001 * self.type) + (0.0005 * self.level)
            )  # Ridotta rispetto all'originale
            if random.random() < chance:
                self.moving_down = True

        if self.moving_down:
            # Muovi verso il giocatore
            self.y += self.speed

            # Muovi anche verso la x del giocatore
            if self.x < player_x:
                self.x += self.speed * 0.5
            elif self.x > player_x:
                self.x -= self.speed * 0.5

            # Se il nemico arriva in fondo, riposizionalo in alto
            if self.y >= SCREEN_HEIGHT:
                self.y = random.randint(-100, -50)
                self.x = random.randint(50, SCREEN_WIDTH - 50)
                self.moving_down = False
                self.move_timer = 0
        else:
            # Movimento laterale standard
            self.x += self.speed

            # Cambia direzione se raggiunge i bordi
            if self.x <= 0 or self.x >= SCREEN_WIDTH - self.width:
                self.speed *= -1
                self.y += 20  # Scende di un po'

        # Animazione
        self.animation_frame += self.animation_speed
        if self.animation_frame >= 2:
            self.animation_frame = 0

    def draw(self, surface):
        # Applica un'animazione semplice (oscillazione)
        oscillation = math.sin(self.animation_frame * 3) * 3

        # Copia l'immagine originale
        image_to_draw = self.image.copy()

        # Ruota leggermente in base all'oscillazione o più se sta attaccando
        angle = oscillation
        if self.moving_down:
            angle = oscillation * 2  # Rotazione più accentuata quando attacca

        if angle != 0:
            image_to_draw = pygame.transform.rotate(image_to_draw, angle)

        surface.blit(image_to_draw, (self.x, self.y))

        # Mostra la barra della vita per nemici con più salute
        if self.health > 1:
            health_pct = self.health / ((self.type + 1) * (1 + (self.level - 1) // 5))
            health_width = int(self.width * health_pct)
            pygame.draw.rect(surface, RED, (self.x, self.y - 5, self.width, 3))
            pygame.draw.rect(surface, GREEN, (self.x, self.y - 5, health_width, 3))

    def get_collision_rect(self):
        return pygame.Rect(self.x + 10, self.y + 10, self.width - 20, self.height - 20)

    def hit(self):
        self.health -= 1
        if self.health <= 0:
            self.active = False
            return True
        return False


# Esplosione
class Explosion:
    def __init__(self, x, y, size=50):
        self.x = x
        self.y = y
        self.size = size
        self.life = 20  # Durata dell'esplosione
        self.current_life = self.life
        self.particles = []

        # Crea particelle dell'esplosione
        num_particles = random.randint(10, 20)
        for _ in range(num_particles):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 5)
            size = random.randint(2, 8)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            color = random.choice([YELLOW, RED, WHITE])
            self.particles.append(
                {"x": x, "y": y, "dx": dx, "dy": dy, "size": size, "color": color}
            )

    def update(self):
        self.current_life -= 1
        for particle in self.particles:
            particle["x"] += particle["dx"]
            particle["y"] += particle["dy"]

    def draw(self, surface):
        for particle in self.particles:
            alpha = int(255 * (self.current_life / self.life))
            color = particle["color"]
            pygame.draw.circle(
                surface,
                (*color, alpha),
                (int(particle["x"]), int(particle["y"])),
                particle["size"],
            )

    def is_active(self):
        return self.current_life > 0


# Power-up
class PowerUp:
    def __init__(self, x, y, power_type):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 30
        self.speed = 2
        self.type = power_type  # 0: triple shot, 1: speed boost, 2: shield
        self.active = True

        # Colori per ogni tipo
        self.colors = [(255, 255, 0), (0, 255, 255), (255, 0, 255)]
        self.color = self.colors[power_type]

        # Effetto glow
        self.glow = create_glow_surface(25, (*self.color, 150))

    def move(self):
        self.y += self.speed
        if self.y > SCREEN_HEIGHT:
            self.active = False

    def draw(self, surface):
        # Disegna il glow
        surface.blit(self.glow, (self.x - 10, self.y - 10))

        # Disegna il corpo
        pygame.draw.circle(
            surface,
            self.color,
            (self.x + self.width // 2, self.y + self.height // 2),
            10,
        )

        # Disegna un simbolo in base al tipo
        if self.type == 0:  # Triple shot
            pygame.draw.line(
                surface,
                WHITE,
                (self.x + 15, self.y + 10),
                (self.x + 15, self.y + 20),
                2,
            )
            pygame.draw.line(
                surface,
                WHITE,
                (self.x + 10, self.y + 10),
                (self.x + 10, self.y + 20),
                2,
            )
            pygame.draw.line(
                surface,
                WHITE,
                (self.x + 20, self.y + 10),
                (self.x + 20, self.y + 20),
                2,
            )
        elif self.type == 1:  # Speed boost
            pygame.draw.polygon(
                surface,
                WHITE,
                [
                    (self.x + 10, self.y + 15),
                    (self.x + 20, self.y + 15),
                    (self.x + 15, self.y + 7),
                ],
            )
        else:  # Shield
            pygame.draw.circle(surface, WHITE, (self.x + 15, self.y + 15), 7, 2)

    def get_collision_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)


# Classe del gioco
class Game:
    def __init__(self):
        self.player = Player()
        self.bullets = []
        self.enemies = []
        self.explosions = []
        self.powerups = []
        self.score = 0
        self.level = 1
        self.game_over = False
        self.paused = False

        # Potenziamenti
        self.triple_shot = False
        self.speed_boost = False
        self.shield = False
        self.shield_duration = 0  # Durata in frame dello scudo (60 frames = 1 secondo)
        self.shield_max_duration = 300  # 5 secondi (ridotto da 10 a 5 secondi)

        # Cuore per mostrare le vite
        self.heart_surface = create_heart_surface()

        # Punti necessari per passare al livello successivo
        self.points_per_level = 1000

        # Timer per la generazione casuale di nemici
        self.enemy_spawn_timer = 0
        # Aumentato il delay per far apparire i nemici meno spesso
        self.enemy_spawn_delay = 180  # 3 secondi (60 FPS) - aumentato da 120
        # Tempo minimo tra la generazione di nemici (crescerà con il livello)
        self.min_enemy_spawn_delay = 60  # Aumentato da 30 a 60 (1 secondo)

        # Impostazioni dei controlli
        self.shoot_key = pygame.K_SPACE  # Tasto per sparare
        self.shoot_cooldown = 0  # Cooldown tra uno sparo e l'altro
        self.shoot_cooldown_max = 15  # Frame di attesa tra gli spari

        # Timer per generare più nemici man mano che il gioco avanza
        self.dynamic_spawn_timer = 0
        # Aumentato l'intervallo per le ondate di nemici
        self.dynamic_spawn_interval = 2700  # Ogni 45 secondi invece di 30

        # Probabilità che un nemico distrutto rilasci un power-up
        self.powerup_chance = 0.15

        # Controllo del numero massimo di nemici attivi contemporaneamente
        self.max_active_enemies = 15  # Limite al numero di nemici attivi

        # Inizializza la prima ondata di nemici
        self.spawn_enemies()

    def spawn_enemies(self):
        per_row = 8
        spacing_x = 80
        spacing_y = 60
        start_x = (SCREEN_WIDTH - (per_row - 1) * spacing_x) // 2
        start_y = 50

        for row in range(3):  # 3 righe
            enemy_type = min(row, 2)  # Limita i tipi a 0, 1, 2
            for col in range(per_row):
                x = start_x + col * spacing_x
                y = start_y + row * spacing_y
                enemy = Enemy(x, y, enemy_type, self.level)
                self.enemies.append(enemy)

    def spawn_random_enemy(self):
        # Controlla se abbiamo già abbastanza nemici
        if len(self.enemies) >= self.max_active_enemies:
            return

        # Genera un nemico casuale nella parte superiore dello schermo
        enemy_type = random.randint(0, 2)
        x = random.randint(50, SCREEN_WIDTH - 50)
        y = random.randint(-100, -50)
        enemy = Enemy(x, y, enemy_type, self.level)
        # Ridotta la probabilità che il nemico scenda subito
        enemy.moving_down = random.random() < 0.2  # Ridotto da 0.4 a 0.2 (20%)
        self.enemies.append(enemy)

    def spawn_wave(self):
        # Controlla se abbiamo già troppi nemici
        current_enemies = len(self.enemies)
        if current_enemies >= self.max_active_enemies:
            return

        # Calcola quanti nemici aggiungere, rispettando il limite massimo
        max_to_add = self.max_active_enemies - current_enemies
        # Ridotto il numero di nemici nell'ondata
        base_enemies = min(2, max_to_add)  # Base di 2 nemici invece di 3-5
        level_bonus = min(
            self.level // 3, max_to_add - base_enemies
        )  # Crescita più lenta
        num_enemies = base_enemies + level_bonus

        # Genera un'ondata di nemici più aggressivi (ma meno numerosi)
        for _ in range(num_enemies):
            enemy_type = random.randint(0, 2)
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = random.randint(-150, -50)
            enemy = Enemy(x, y, enemy_type, self.level)
            enemy.moving_down = True  # Tutti i nemici dell'ondata attaccano subito
            # Velocità leggermente aumentata per i nemici dell'ondata
            enemy.speed *= 1.2
            self.enemies.append(enemy)

    def check_collisions(self):
        # Collisioni proiettili-nemici
        for bullet in self.bullets:
            if not bullet.active:
                continue

            bullet_rect = pygame.Rect(bullet.x, bullet.y, bullet.width, bullet.height)

            for enemy in self.enemies:
                if not enemy.active:
                    continue

                if bullet_rect.colliderect(enemy.get_collision_rect()):
                    bullet.active = False
                    if enemy.hit():  # Se il nemico è distrutto
                        self.score += (enemy.type + 1) * 100
                        self.explosions.append(
                            Explosion(
                                enemy.x + enemy.width // 2, enemy.y + enemy.height // 2
                            )
                        )

                        # Possibilità di rilasciare un power-up
                        if random.random() < self.powerup_chance:
                            powerup_type = random.randint(0, 2)
                            self.powerups.append(
                                PowerUp(enemy.x, enemy.y, powerup_type)
                            )

                        # Verifica se è stato raggiunto il punteggio per il livello successivo
                        if self.score >= self.level * self.points_per_level:
                            self.level_up()
                    break

        # Collisioni giocatore-nemici
        player_rect = self.player.get_collision_rect()
        for enemy in self.enemies:
            if not enemy.active:
                continue

            if player_rect.colliderect(enemy.get_collision_rect()):
                if (
                    not self.shield
                ):  # Il giocatore perde una vita solo se non ha lo scudo
                    self.player.lives -= 1
                    self.explosions.append(
                        Explosion(
                            enemy.x + enemy.width // 2, enemy.y + enemy.height // 2
                        )
                    )
                    enemy.active = False

                    if self.player.lives <= 0:
                        self.game_over = True
                else:
                    # Lo scudo blocca l'impatto ma si disattiva
                    self.explosions.append(
                        Explosion(
                            enemy.x + enemy.width // 2, enemy.y + enemy.height // 2
                        )
                    )
                    enemy.active = False
                    self.shield = False
                    self.shield_duration = 0

        # Collisioni giocatore-powerup
        for powerup in self.powerups:
            if not powerup.active:
                continue

            if player_rect.colliderect(powerup.get_collision_rect()):
                powerup.active = False
                if powerup.type == 0:  # Triple shot
                    self.triple_shot = True
                elif powerup.type == 1:  # Speed boost
                    self.speed_boost = True
                    self.player.speed = 8  # Velocità aumentata
                else:  # Shield
                    self.shield = True
                    self.shield_duration = self.shield_max_duration  # Resetta la durata

    def level_up(self):
        self.level += 1
        # Mostra un effetto per il passaggio di livello
        level_up_text = big_font.render(f"LIVELLO {self.level}!", True, YELLOW)
        screen.blit(
            level_up_text,
            (
                SCREEN_WIDTH // 2 - level_up_text.get_width() // 2,
                SCREEN_HEIGHT // 2 - level_up_text.get_height() // 2,
            ),
        )
        pygame.display.flip()
        pygame.time.wait(1000)  # Pausa di 1 secondo

        # Diminuisce il tempo di spawn dei nemici con l'aumentare del livello,
        # ma in modo meno aggressivo rispetto al codice originale
        self.enemy_spawn_delay = max(180 - (self.level * 5), self.min_enemy_spawn_delay)

        # Aumenta progressivamente il numero massimo di nemici con il livello
        # ma con un cap per evitare che diventino troppi
        self.max_active_enemies = min(15 + (self.level // 2), 25)

        # Genera immediatamente un'ondata di nemici per celebrare il nuovo livello
        self.spawn_wave()

    def update(self):
        if self.game_over or self.paused:
            return

        # Aggiorna il cooldown dello sparo
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        # Aggiorna la durata dello scudo
        if self.shield:
            self.shield_duration -= 1
            if self.shield_duration <= 0:
                self.shield = False

        # Gestione dello spawn casuale di nemici
        self.enemy_spawn_timer += 1
        if self.enemy_spawn_timer >= self.enemy_spawn_delay:
            self.enemy_spawn_timer = 0
            # Aggiungiamo un controllo per non generare troppi nemici
            if len(self.enemies) < self.max_active_enemies:
                self.spawn_random_enemy()

        # Timer per generare ondate di nemici
        self.dynamic_spawn_timer += 1
        if self.dynamic_spawn_timer >= self.dynamic_spawn_interval:
            self.dynamic_spawn_timer = 0
            self.spawn_wave()

        # Muovi gli oggetti
        for bullet in self.bullets:
            bullet.move()

        # Ottieni la posizione x del giocatore per il movimento dei nemici
        player_x = self.player.x + self.player.width // 2

        for enemy in self.enemies:
            if enemy.active:
                enemy.move(player_x)

        for explosion in self.explosions:
            explosion.update()

        for powerup in self.powerups:
            powerup.move()

        # Pulisci gli oggetti inattivi
        self.bullets = [b for b in self.bullets if b.active]
        self.enemies = [e for e in self.enemies if e.active]
        self.explosions = [e for e in self.explosions if e.is_active()]
        self.powerups = [p for p in self.powerups if p.active]

        # Verifica collisioni
        self.check_collisions()

    def draw(self, surface):
        # Disegna lo sfondo
        surface.fill(BLACK)

        # Disegna le stelle
        for star in stars:
            x, y, size, brightness = star
            pygame.draw.circle(
                surface, (brightness, brightness, brightness), (x, y), size
            )

        # Disegna gli oggetti del gioco
        for bullet in self.bullets:
            bullet.draw(surface)

        for enemy in self.enemies:
            if enemy.active:
                enemy.draw(surface)

        for explosion in self.explosions:
            explosion.draw(surface)

        for powerup in self.powerups:
            powerup.draw(surface)

        self.player.draw(surface)

        # Disegna lo scudo se attivo
        if self.shield:
            shield_radius = 40
            shield_surface = pygame.Surface(
                (shield_radius * 2, shield_radius * 2), pygame.SRCALPHA
            )

            # Aggiungi un effetto di "lampeggio" quando lo scudo sta per finire
            alpha = 100
            if self.shield_duration < 120:  # Lampeggia negli ultimi 2 secondi
                alpha = int(
                    100 * (0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.01))
                )

            pygame.draw.circle(
                shield_surface,
                (100, 200, 255, alpha),
                (shield_radius, shield_radius),
                shield_radius,
            )
            surface.blit(
                shield_surface,
                (
                    self.player.x + self.player.width // 2 - shield_radius,
                    self.player.y + self.player.height // 2 - shield_radius,
                ),
            )

        # Disegna l'interfaccia utente
        # Punteggio
        score_text = font.render(f"Punteggio: {self.score}", True, WHITE)
        surface.blit(score_text, (10, 10))

        # Livello
        level_text = font.render(f"Livello: {self.level}", True, WHITE)
        surface.blit(level_text, (10, 40))

        # Vite
        for i in range(self.player.lives):
            surface.blit(self.heart_surface, (10 + i * 30, 70))

        # Potenziamenti attivi
        powerup_text = []
        if self.triple_shot:
            powerup_text.append("Triple Shot")
        if self.speed_boost:
            powerup_text.append("Speed Boost")
        if self.shield:
            # Mostra anche la durata rimanente dello scudo
            shield_time = int(self.shield_duration / 60)  # Converte frame in secondi
            powerup_text.append(f"Shield ({shield_time}s)")

        if powerup_text:
            text = "Potenziamenti: " + ", ".join(powerup_text)
            bonus_text = font.render(text, True, YELLOW)
            surface.blit(bonus_text, (10, 100))

        # Se il gioco è in pausa
        if self.paused:
            pause_overlay = pygame.Surface(
                (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA
            )
            pause_overlay.fill((0, 0, 0, 128))
            surface.blit(pause_overlay, (0, 0))

            pause_text = big_font.render("PAUSA", True, WHITE)
            surface.blit(
                pause_text,
                (
                    SCREEN_WIDTH // 2 - pause_text.get_width() // 2,
                    SCREEN_HEIGHT // 2 - pause_text.get_height() // 2,
                ),
            )

            continue_text = font.render("Premi P per continuare", True, WHITE)
            surface.blit(
                continue_text,
                (
                    SCREEN_WIDTH // 2 - continue_text.get_width() // 2,
                    SCREEN_HEIGHT // 2 + 50,
                ),
            )

        # Se il gioco è finito
        if self.game_over:
            game_over_overlay = pygame.Surface(
                (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA
            )
            game_over_overlay.fill((0, 0, 0, 180))
            surface.blit(game_over_overlay, (0, 0))

            game_over_text = big_font.render("GAME OVER", True, RED)
            surface.blit(
                game_over_text,
                (
                    SCREEN_WIDTH // 2 - game_over_text.get_width() // 2,
                    SCREEN_HEIGHT // 2 - game_over_text.get_height() // 2,
                ),
            )

            final_score_text = font.render(
                f"Punteggio Finale: {self.score}", True, WHITE
            )
            surface.blit(
                final_score_text,
                (
                    SCREEN_WIDTH // 2 - final_score_text.get_width() // 2,
                    SCREEN_HEIGHT // 2 + 50,
                ),
            )

            restart_text = font.render("Premi R per ricominciare", True, WHITE)
            surface.blit(
                restart_text,
                (
                    SCREEN_WIDTH // 2 - restart_text.get_width() // 2,
                    SCREEN_HEIGHT // 2 + 100,
                ),
            )

    def shoot(self):
        if self.shoot_cooldown == 0:
            player_center_x = self.player.x + self.player.width // 2
            player_top = self.player.y

            if self.triple_shot:
                # Spara tre proiettili
                self.bullets.append(Bullet(player_center_x - 20, player_top))
                self.bullets.append(Bullet(player_center_x, player_top))
                self.bullets.append(Bullet(player_center_x + 20, player_top))
            else:
                # Spara un solo proiettile
                self.bullets.append(Bullet(player_center_x, player_top))

            self.shoot_cooldown = self.shoot_cooldown_max

    def reset(self):
        self.__init__()  # Reinizializza il gioco


# Loop principale
def main():
    clock = pygame.time.Clock()
    game = Game()
    running = True

    # Controlli per muoversi (possibilità di tenere premuto)
    left_pressed = False
    right_pressed = False

    while running:
        # Gestione eventi
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    left_pressed = True
                elif event.key == pygame.K_RIGHT:
                    right_pressed = True

                # Sparo (può essere anche tenuto premuto)
                elif event.key == game.shoot_key:
                    if not game.paused and not game.game_over:
                        game.shoot()

                # Pausa
                elif event.key == pygame.K_p:
                    game.paused = not game.paused

                # Riavvio se game over
                elif event.key == pygame.K_r and game.game_over:
                    game.reset()

                # Uscita
                elif event.key == pygame.K_ESCAPE:
                    running = False

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    left_pressed = False
                elif event.key == pygame.K_RIGHT:
                    right_pressed = False

        # Movimento continuo se tasti tenuti premuti
        if not game.paused and not game.game_over:
            if left_pressed:
                game.player.move("left")
            if right_pressed:
                game.player.move("right")

            # Sparo continuo se spazio tenuto premuto
            keys = pygame.key.get_pressed()
            if keys[game.shoot_key]:
                game.shoot()

        # Aggiorna il gioco
        game.update()

        # Disegna tutto
        game.draw(screen)

        # Aggiorna lo schermo
        pygame.display.flip()

        # Limita a 60 FPS
        clock.tick(60)

    # Chiudi pygame
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
