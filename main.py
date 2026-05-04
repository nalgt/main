import pygame
import math
import sys
import random

# ── Constants ──────────────────────────────────────────────────────
WIDTH, HEIGHT   = 960, 540
HALF_H          = HEIGHT // 2
FOV             = math.pi / 3          # 60 degrees
HALF_FOV        = FOV / 2
NUM_RAYS        = WIDTH // 2           # cast every 2 pixels for speed
MAX_DEPTH       = 20
DELTA_ANGLE     = FOV / NUM_RAYS
SCALE           = WIDTH // NUM_RAYS
SCREEN_DIST     = (WIDTH / 2) / math.tan(HALF_FOV)
TILE            = 64
PLAYER_SPEED    = 3.0
ROT_SPEED       = 0.035
FPS             = 60

# ── Colours ────────────────────────────────────────────────────────
BLACK    = (0, 0, 0)
WHITE    = (255, 255, 255)
RED      = (220, 30, 30)
GREEN    = (30, 200, 30)
BLUE     = (30, 30, 220)
YELLOW   = (255, 200, 0)
GREY     = (100, 100, 100)
DARKGREY = (50, 50, 50)
CEILING  = (20, 20, 30)
FLOOR    = (40, 35, 30)
HUD_BG   = (10, 10, 15)

WALL_COLORS = {
    1: (160, 40,  40),   # red brick
    2: (40,  160, 40),   # green stone
    3: (40,  40,  160),  # blue metal
    4: (160, 160, 40),   # yellow/gold
    5: (120, 80,  40),   # brown wood
    6: (80,  80,  80),   # grey concrete
}

# ── Map (0=empty, 1-6=wall, 7=door) ───────────────────────────────
MAP = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,2,2,0,0,0,0,7,0,0,0,3,3,3,0,0,0,1],
    [1,0,0,2,0,0,0,0,0,0,0,0,0,3,0,3,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,3,0,3,0,0,0,1],
    [1,0,0,0,0,5,5,5,0,1,1,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,5,0,5,0,0,0,0,0,0,0,0,4,4,0,1],
    [1,0,0,0,0,5,0,5,0,0,0,0,0,0,0,0,4,0,0,1],
    [1,0,0,0,0,5,5,5,0,0,0,6,6,0,0,0,4,4,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,6,0,0,0,0,0,0,0,1],
    [1,0,0,6,0,0,0,0,0,0,0,6,0,0,0,0,0,0,0,1],
    [1,0,0,6,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,1,1,0,0,0,5,0,5,0,0,1],
    [1,0,0,0,0,0,2,0,0,1,0,0,0,0,5,0,5,0,0,1],
    [1,0,0,0,0,0,2,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,3,3,3,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
]
MAP_W = len(MAP[0])
MAP_H = len(MAP)

def is_wall(x, y):
    mx, my = int(x // TILE), int(y // TILE)
    if 0 <= mx < MAP_W and 0 <= my < MAP_H:
        return MAP[my][mx] != 0
    return True

def get_tile(x, y):
    mx, my = int(x // TILE), int(y // TILE)
    if 0 <= mx < MAP_W and 0 <= my < MAP_H:
        return MAP[my][mx]
    return 1

# ── Enemy ──────────────────────────────────────────────────────────
class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.hp       = 3
        self.alive    = True
        self.angle    = 0
        self.speed    = 0.6
        self.shoot_cd = 0
        self.alert    = False
        self.size     = 24
        self.color    = (200, 30, 30)
        self.shirt    = (80, 60, 40)

    def update(self, player, dt):
        if not self.alive:
            return
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)
        self.angle = math.atan2(dy, dx)

        if dist < 400:
            self.alert = True

        if self.alert:
            if dist > 60:
                nx = self.x + math.cos(self.angle) * self.speed
                ny = self.y + math.sin(self.angle) * self.speed
                if not is_wall(nx, ny):
                    self.x, self.y = nx, ny
                elif not is_wall(nx, self.y):
                    self.x = nx
                elif not is_wall(self.x, ny):
                    self.y = ny

            if self.shoot_cd <= 0 and dist < 300:
                self.shoot_cd = 90
                return True  # hit player
            if self.shoot_cd > 0:
                self.shoot_cd -= 1
        return False

    def draw_sprite(self, screen, player, z_buffer):
        if not self.alive:
            return
        dx = self.x - player.x
        dy = self.y - player.y
        dist = math.hypot(dx, dy)
        if dist < 1:
            return

        # Sprite angle relative to player
        sprite_angle = math.atan2(dy, dx) - player.angle
        # Normalise
        while sprite_angle > math.pi:  sprite_angle -= 2*math.pi
        while sprite_angle < -math.pi: sprite_angle += 2*math.pi

        if abs(sprite_angle) > FOV / 1.5:
            return

        # Screen X
        screen_x = int((WIDTH/2) * (1 + sprite_angle / HALF_FOV))
        sprite_h = min(int(SCREEN_DIST / (dist + 0.0001) * TILE * 0.8), HEIGHT)
        sprite_w = sprite_h

        x0 = screen_x - sprite_w // 2
        y0 = HALF_H - sprite_h // 2

        col_start = max(0, x0)
        col_end   = min(WIDTH, x0 + sprite_w)

        for col in range(col_start, col_end):
            ray = col // SCALE
            if ray < len(z_buffer) and dist < z_buffer[ray]:
                tx = (col - x0) / sprite_w
                # Simple sprite: body + head
                head_y = y0
                body_y = y0 + sprite_h // 3
                head_r = sprite_h // 5
                body_h = sprite_h * 2 // 3
                body_w = sprite_w // 3

                # Draw body column
                bx0 = screen_x - body_w//2
                bx1 = screen_x + body_w//2
                if bx0 <= col <= bx1:
                    pygame.draw.line(screen, self.shirt,
                        (col, body_y), (col, body_y + body_h), 1)
                # Draw head column
                hx0 = screen_x - head_r
                hx1 = screen_x + head_r
                if hx0 <= col <= hx1:
                    pygame.draw.line(screen, (220,180,130),
                        (col, head_y), (col, head_y + head_r*2), 1)

        # HP bar
        if dist < 250:
            bar_w = 30
            bar_x = screen_x - bar_w//2
            bar_y = y0 - 12
            pygame.draw.rect(screen, RED,    (bar_x, bar_y, bar_w, 5))
            pygame.draw.rect(screen, GREEN,  (bar_x, bar_y, int(bar_w * self.hp/3), 5))

# ── Pickup ─────────────────────────────────────────────────────────
class Pickup:
    def __init__(self, x, y, kind):
        self.x = x; self.y = y; self.kind = kind
        self.active = True
        self.bob = 0

    def try_collect(self, player):
        if not self.active: return
        if math.hypot(self.x - player.x, self.y - player.y) < 32:
            self.active = False
            if self.kind == 'health':
                player.hp = min(100, player.hp + 25)
            elif self.kind == 'ammo':
                player.ammo += 15
            elif self.kind == 'key':
                player.keys += 1

    def draw_sprite(self, screen, player, z_buffer):
        if not self.active: return
        self.bob = (self.bob + 0.05) % (math.pi * 2)
        dx = self.x - player.x
        dy = self.y - player.y
        dist = math.hypot(dx, dy)
        if dist < 1 or dist > 400: return

        sprite_angle = math.atan2(dy, dx) - player.angle
        while sprite_angle >  math.pi: sprite_angle -= 2*math.pi
        while sprite_angle < -math.pi: sprite_angle += 2*math.pi
        if abs(sprite_angle) > FOV / 1.5: return

        screen_x = int((WIDTH/2) * (1 + sprite_angle / HALF_FOV))
        sz = min(int(SCREEN_DIST / (dist+0.001) * 24), 60)
        bob_off = int(math.sin(self.bob) * 3)
        cy = HALF_H + bob_off

        ray = screen_x // SCALE
        if 0 <= ray < len(z_buffer) and dist < z_buffer[ray]:
            color = {'health': (220,50,50), 'ammo': (220,220,50), 'key': (255,200,0)}[self.kind]
            pygame.draw.circle(screen, color, (screen_x, cy), max(4, sz//2))
            pygame.draw.circle(screen, WHITE, (screen_x, cy), max(4, sz//2), 1)

# ── Player ─────────────────────────────────────────────────────────
class Player:
    def __init__(self):
        self.x      = TILE * 2.5
        self.y      = TILE * 2.5
        self.angle  = 0.0
        self.hp     = 100
        self.ammo   = 30
        self.keys   = 0
        self.score  = 0
        self.weapon_anim = 0
        self.shot_cd     = 0
        self.hurt_flash  = 0

    def move(self, keys_pressed, dt):
        s = PLAYER_SPEED
        dx = dy = 0
        if keys_pressed[pygame.K_w] or keys_pressed[pygame.K_UP]:
            dx += math.cos(self.angle) * s
            dy += math.sin(self.angle) * s
        if keys_pressed[pygame.K_s] or keys_pressed[pygame.K_DOWN]:
            dx -= math.cos(self.angle) * s
            dy -= math.sin(self.angle) * s
        if keys_pressed[pygame.K_a]:
            dx += math.cos(self.angle - math.pi/2) * s
            dy += math.sin(self.angle - math.pi/2) * s
        if keys_pressed[pygame.K_d]:
            dx += math.cos(self.angle + math.pi/2) * s
            dy += math.sin(self.angle + math.pi/2) * s
        if keys_pressed[pygame.K_LEFT]:
            self.angle -= ROT_SPEED
        if keys_pressed[pygame.K_RIGHT]:
            self.angle += ROT_SPEED

        margin = 16
        nx = self.x + dx
        ny = self.y + dy
        if not is_wall(nx + math.copysign(margin,dx), self.y):
            self.x = nx
        if not is_wall(self.x, ny + math.copysign(margin,dy)):
            self.y = ny

        if self.shot_cd  > 0: self.shot_cd  -= 1
        if self.hurt_flash > 0: self.hurt_flash -= 1
        if self.weapon_anim > 0: self.weapon_anim -= 1

    def shoot(self, enemies):
        if self.ammo <= 0 or self.shot_cd > 0:
            return
        self.ammo -= 1
        self.shot_cd = 15
        self.weapon_anim = 10
        # Check hit
        for e in enemies:
            if not e.alive: continue
            dx = e.x - self.x
            dy = e.y - self.y
            dist = math.hypot(dx, dy)
            if dist > 300: continue
            angle_to = math.atan2(dy, dx)
            diff = abs(angle_to - self.angle) % (2*math.pi)
            if diff > math.pi: diff = 2*math.pi - diff
            if diff < 0.25:
                e.hp -= 1
                self.score += 10
                if e.hp <= 0:
                    e.alive = False
                    self.score += 50

# ── Raycaster ──────────────────────────────────────────────────────
class Raycaster:
    def __init__(self, screen):
        self.screen = screen

    def cast(self, player):
        z_buffer = []
        ray_angle = player.angle - HALF_FOV + 0.0001

        for ray in range(NUM_RAYS):
            cos_a = math.cos(ray_angle)
            sin_a = math.sin(ray_angle)

            # DDA algorithm
            # Ray direction
            if cos_a == 0: cos_a = 1e-6
            if sin_a == 0: sin_a = 1e-6

            # Map cell
            map_x = int(player.x // TILE)
            map_y = int(player.y // TILE)

            # Delta distances
            delta_x = abs(1 / cos_a)
            delta_y = abs(1 / sin_a)

            # Step and initial side dist
            if cos_a < 0:
                step_x = -1
                side_x = (player.x - map_x * TILE) / TILE * delta_x
            else:
                step_x = 1
                side_x = ((map_x + 1) * TILE - player.x) / TILE * delta_x

            if sin_a < 0:
                step_y = -1
                side_y = (player.y - map_y * TILE) / TILE * delta_y
            else:
                step_y = 1
                side_y = ((map_y + 1) * TILE - player.y) / TILE * delta_y

            # DDA march
            depth = 0
            side = 0
            for _ in range(MAX_DEPTH * 10):
                if side_x < side_y:
                    side_x += delta_x
                    map_x  += step_x
                    side = 0
                else:
                    side_y += delta_y
                    map_y  += step_y
                    side = 1

                if 0 <= map_x < MAP_W and 0 <= map_y < MAP_H:
                    if MAP[map_y][map_x] != 0:
                        tile_type = MAP[map_y][map_x]
                        if side == 0:
                            depth = (map_x - int(player.x//TILE) + (1 - step_x)//2) / cos_a * TILE
                        else:
                            depth = (map_y - int(player.y//TILE) + (1 - step_y)//2) / sin_a * TILE
                        break
                else:
                    depth = MAX_DEPTH * TILE
                    tile_type = 1
                    break

            # Fish-eye correction
            depth *= math.cos(player.angle - ray_angle)
            depth = max(1, depth)

            # Wall height
            wall_h = min(int(SCREEN_DIST * TILE / depth), HEIGHT)
            wall_top    = HALF_H - wall_h // 2
            wall_bottom = HALF_H + wall_h // 2

            # Color
            base_col = WALL_COLORS.get(tile_type, (120,120,120))
            shade = max(0.15, min(1.0, 1.0 - depth / (MAX_DEPTH * TILE * 0.7)))
            if side == 1: shade *= 0.65  # darker N/S sides
            r = int(base_col[0] * shade)
            g = int(base_col[1] * shade)
            b = int(base_col[2] * shade)

            col_x = ray * SCALE

            # Ceiling
            pygame.draw.rect(self.screen, CEILING, (col_x, 0, SCALE, wall_top))
            # Wall
            pygame.draw.rect(self.screen, (r,g,b), (col_x, wall_top, SCALE, wall_h))
            # Floor
            pygame.draw.rect(self.screen, FLOOR, (col_x, wall_bottom, SCALE, HEIGHT - wall_bottom))

            z_buffer.append(depth)
            ray_angle += DELTA_ANGLE

        return z_buffer

# ── HUD ────────────────────────────────────────────────────────────
def draw_weapon(screen, player):
    # Simple pixel-art gun
    anim = player.weapon_anim
    gun_x = WIDTH // 2 + 40
    gun_y = HEIGHT - 120 + (anim * 3)

    # Barrel
    pygame.draw.rect(screen, (80,80,80),  (gun_x, gun_y, 12, 50))
    pygame.draw.rect(screen, (60,60,60),  (gun_x+2, gun_y, 8, 50))
    # Handle
    pygame.draw.rect(screen, (50,35,20),  (gun_x-4, gun_y+35, 20, 30))
    # Trigger guard
    pygame.draw.rect(screen, (70,50,30),  (gun_x-2, gun_y+45, 14, 8))
    # Muzzle flash
    if anim > 6:
        pygame.draw.circle(screen, YELLOW, (gun_x+6, gun_y-5), 10)
        pygame.draw.circle(screen, WHITE,  (gun_x+6, gun_y-5), 5)

def draw_hud(screen, player, font, small_font):
    # HUD bar
    pygame.draw.rect(screen, HUD_BG, (0, HEIGHT-50, WIDTH, 50))
    pygame.draw.line(screen, (40,40,60), (0, HEIGHT-50), (WIDTH, HEIGHT-50), 1)

    # HP
    hp_col = GREEN if player.hp > 50 else YELLOW if player.hp > 25 else RED
    pygame.draw.rect(screen, (30,30,30), (10, HEIGHT-38, 150, 20))
    pygame.draw.rect(screen, hp_col,    (10, HEIGHT-38, int(150*player.hp/100), 20))
    pygame.draw.rect(screen, WHITE,     (10, HEIGHT-38, 150, 20), 1)
    screen.blit(small_font.render(f'HP: {player.hp}', True, WHITE), (14, HEIGHT-36))

    # Ammo
    ammo_surf = font.render(f'AMMO: {player.ammo}', True, YELLOW)
    screen.blit(ammo_surf, (200, HEIGHT-42))

    # Score
    score_surf = font.render(f'SCORE: {player.score}', True, WHITE)
    screen.blit(score_surf, (400, HEIGHT-42))

    # Keys
    key_surf = font.render(f'KEYS: {player.keys}', True, (255,200,0))
    screen.blit(key_surf, (650, HEIGHT-42))

    # Crosshair
    cx, cy = WIDTH//2, HEIGHT//2
    pygame.draw.line(screen, WHITE, (cx-12, cy), (cx+12, cy), 1)
    pygame.draw.line(screen, WHITE, (cx, cy-12), (cx, cy+12), 1)
    pygame.draw.circle(screen, WHITE, (cx, cy), 3, 1)

    # Hurt flash
    if player.hurt_flash > 0:
        flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        alpha = int(120 * player.hurt_flash / 20)
        flash.fill((200, 0, 0, alpha))
        screen.blit(flash, (0,0))

def draw_minimap(screen, player):
    mscale = 5
    ox, oy = 10, 10
    for y in range(MAP_H):
        for x in range(MAP_W):
            col = DARKGREY if MAP[y][x] == 0 else WALL_COLORS.get(MAP[y][x], GREY)
            pygame.draw.rect(screen, col, (ox+x*mscale, oy+y*mscale, mscale-1, mscale-1))
    # Player dot
    px = ox + int(player.x / TILE * mscale)
    py = oy + int(player.y / TILE * mscale)
    pygame.draw.circle(screen, GREEN, (px, py), 3)
    # Direction
    ex = px + int(math.cos(player.angle) * 6)
    ey = py + int(math.sin(player.angle) * 6)
    pygame.draw.line(screen, YELLOW, (px, py), (ex, ey), 1)

# ── Screens ────────────────────────────────────────────────────────
def draw_title(screen, font_big, font):
    screen.fill((10, 0, 0))
    # Nazi-ish red title bar
    pygame.draw.rect(screen, (180, 0, 0), (0, HEIGHT//3 - 60, WIDTH, 80))
    title = font_big.render("WOLFENSTEIN 3D", True, YELLOW)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//3 - 50))
    sub = font.render("Python Raycasting Edition", True, WHITE)
    screen.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//3 + 40))
    inst = font.render("WASD / Arrows = Move    SPACE = Shoot    M = Map    ESC = Quit", True, GREY)
    screen.blit(inst, (WIDTH//2 - inst.get_width()//2, HEIGHT*2//3))
    start = font.render("Press ENTER to start", True, YELLOW)
    screen.blit(start, (WIDTH//2 - start.get_width()//2, HEIGHT*2//3 + 40))

def draw_gameover(screen, font_big, font, score, won=False):
    screen.fill((10, 0, 0) if not won else (0, 10, 0))
    msg = "MISSION COMPLETE!" if won else "YOU DIED!"
    col = YELLOW if won else RED
    t = font_big.render(msg, True, col)
    screen.blit(t, (WIDTH//2 - t.get_width()//2, HEIGHT//3))
    s = font.render(f"Final Score: {score}", True, WHITE)
    screen.blit(s, (WIDTH//2 - s.get_width()//2, HEIGHT//2))
    r = font.render("Press ENTER to restart", True, GREY)
    screen.blit(r, (WIDTH//2 - r.get_width()//2, HEIGHT*2//3))

# ── Main ───────────────────────────────────────────────────────────
def make_entities():
    enemies = [
        Enemy(TILE*8.5,  TILE*3.5),
        Enemy(TILE*13.5, TILE*5.5),
        Enemy(TILE*3.5,  TILE*12.5),
        Enemy(TILE*10.5, TILE*10.5),
        Enemy(TILE*16.5, TILE*15.5),
        Enemy(TILE*6.5,  TILE*17.5),
    ]
    pickups = [
        Pickup(TILE*4.5,  TILE*8.5,  'health'),
        Pickup(TILE*12.5, TILE*3.5,  'ammo'),
        Pickup(TILE*17.5, TILE*7.5,  'health'),
        Pickup(TILE*2.5,  TILE*15.5, 'ammo'),
        Pickup(TILE*15.5, TILE*12.5, 'key'),
        Pickup(TILE*9.5,  TILE*14.5, 'health'),
        Pickup(TILE*7.5,  TILE*6.5,  'ammo'),
    ]
    return enemies, pickups

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Wolfenstein 3D — Python")
    clock  = pygame.time.Clock()
    pygame.mouse.set_visible(False)

    try:
        font_big   = pygame.font.SysFont('Arial', 64, bold=True)
        font       = pygame.font.SysFont('Arial', 22, bold=True)
        small_font = pygame.font.SysFont('Arial', 16)
    except:
        font_big   = pygame.font.Font(None, 64)
        font       = pygame.font.Font(None, 28)
        small_font = pygame.font.Font(None, 20)

    raycaster = Raycaster(screen)

    state      = 'title'   # title / game / dead / win
    player     = Player()
    enemies, pickups = make_entities()
    show_map   = False

    while True:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

                if state == 'title' and event.key == pygame.K_RETURN:
                    state = 'game'
                    player = Player()
                    enemies, pickups = make_entities()

                elif state in ('dead','win') and event.key == pygame.K_RETURN:
                    state = 'title'

                elif state == 'game':
                    if event.key == pygame.K_SPACE:
                        player.shoot(enemies)
                    if event.key == pygame.K_m:
                        show_map = not show_map

        if state == 'title':
            draw_title(screen, font_big, font)

        elif state == 'game':
            keys = pygame.key.get_pressed()
            player.move(keys, dt)

            # Mouse look
            mx, _ = pygame.mouse.get_rel()
            player.angle += mx * 0.002

            # Cast rays
            z_buffer = raycaster.cast(player)

            # Pickups
            for p in pickups:
                p.try_collect(player)
                p.draw_sprite(screen, player, z_buffer)

            # Enemies
            for e in enemies:
                hit = e.update(player, dt)
                if hit and player.hurt_flash == 0:
                    player.hp -= random.randint(8, 18)
                    player.hurt_flash = 20
                e.draw_sprite(screen, player, z_buffer)

            # Weapon
            draw_weapon(screen, player)
            draw_hud(screen, player, font, small_font)

            if show_map:
                draw_minimap(screen, player)

            # Win condition
            if all(not e.alive for e in enemies):
                state = 'win'

            # Death
            if player.hp <= 0:
                player.hp = 0
                state = 'dead'

        elif state == 'dead':
            draw_gameover(screen, font_big, font, player.score, won=False)

        elif state == 'win':
            draw_gameover(screen, font_big, font, player.score, won=True)

        pygame.display.flip()

if __name__ == '__main__':
    main()
