import math
import random
from dataclasses import dataclass

import pyxel


WIDTH = 256
HEIGHT = 224
CENTER_X = WIDTH // 2
CENTER_Y = HEIGHT // 2
FOV = 140.0
NEAR_Z = 2.0

STATE_TITLE = 0
STATE_GAME = 1
STATE_GAME_OVER = 2


@dataclass
class Enemy:
    x: float
    y: float
    z: float
    size: float
    rot: float
    rot_speed: float
    speed: float


@dataclass
class Bullet:
    x: float
    y: float
    z: float
    speed: float
    ray_x: float
    ray_y: float


@dataclass
class Star:
    x: float
    y: float
    z: float
    speed: float


@dataclass
class Debris:
    x: float
    y: float
    z: float
    vx: float
    vy: float
    vz: float
    life: int
    max_life: int


class App:
    def __init__(self) -> None:
        pyxel.init(WIDTH, HEIGHT, title="Pyxel 3D Shooting", fps=60)

        self.state = STATE_TITLE
        self.frame = 0

        self.high_score = 0
        self.new_high_score = False

        self.player_x = 0.0
        self.player_y = 0.0
        self.player_z = 26.0
        self.player_size = 3.5
        self.player_speed = 1.8
        self.forward_speed = 1.2

        self.hp = 100
        self.score = 0
        self.damage_flash_timer = 0

        self.enemy_spawn_timer = 0
        self.bullet_cooldown = 0

        self.enemies: list[Enemy] = []
        self.bullets: list[Bullet] = []
        self.stars: list[Star] = []
        self.debris: list[Debris] = []

        self.reset_stars()

        pyxel.run(self.update, self.draw)

    def reset_stars(self) -> None:
        self.stars = []
        for _ in range(120):
            self.stars.append(self.make_star(random.uniform(8.0, 260.0)))

    def make_star(self, z: float = 260.0) -> Star:
        return Star(
            x=random.uniform(-170.0, 170.0),
            y=random.uniform(-170.0, 170.0),
            z=z,
            speed=random.uniform(0.8, 2.0),
        )

    def reset_game(self) -> None:
        self.player_x = 0.0
        self.player_y = 0.0

        self.hp = 100
        self.score = 0
        self.enemy_spawn_timer = 0
        self.bullet_cooldown = 0
        self.damage_flash_timer = 0

        self.enemies.clear()
        self.bullets.clear()
        self.debris.clear()
        self.reset_stars()

        self.new_high_score = False
        self.state = STATE_GAME

    def project(self, x: float, y: float, z: float) -> tuple[float, float] | None:
        if z <= NEAR_Z:
            return None
        sx = CENTER_X + (x * FOV / z)
        sy = CENTER_Y - (y * FOV / z)
        return sx, sy

    def rotate_y(self, x: float, z: float, a: float) -> tuple[float, float]:
        ca = math.cos(a)
        sa = math.sin(a)
        return x * ca - z * sa, x * sa + z * ca

    def update(self) -> None:
        self.frame += 1

        if self.state == STATE_TITLE:
            self.update_title()
        elif self.state == STATE_GAME:
            self.update_game()
        else:
            self.update_game_over()

    def is_action_pressed(self) -> bool:
        return pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A)

    def is_action_held(self) -> bool:
        return pyxel.btn(pyxel.KEY_SPACE) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_A)

    def update_title(self) -> None:
        if self.is_action_pressed():
            self.reset_game()

    def update_game_over(self) -> None:
        if self.is_action_pressed():
            self.state = STATE_TITLE

    def update_game(self) -> None:
        if self.damage_flash_timer > 0:
            self.damage_flash_timer -= 1

        self.update_player()
        self.update_stars()
        self.spawn_enemy()
        self.update_enemies()
        self.update_bullets()
        self.update_debris()
        self.check_collisions()

        if self.hp <= 0:
            if self.score > self.high_score:
                self.high_score = self.score
                self.new_high_score = True
            self.state = STATE_GAME_OVER

    def update_player(self) -> None:
        if pyxel.btn(pyxel.KEY_LEFT):
            self.player_x -= self.player_speed
        if pyxel.btn(pyxel.KEY_RIGHT):
            self.player_x += self.player_speed
        if pyxel.btn(pyxel.KEY_UP):
            self.player_y += self.player_speed
        if pyxel.btn(pyxel.KEY_DOWN):
            self.player_y -= self.player_speed

        # Keep the whole ship inside the visible play area in screen space.
        margin_x = 2.0
        margin_top = 14.0
        margin_bottom = 2.0

        wing_extent_x = self.player_size * 2.0
        body_extent_y = self.player_size

        left_world = ((margin_x - CENTER_X) * self.player_z / FOV) + wing_extent_x
        right_world = (((WIDTH - 1 - margin_x) - CENTER_X) * self.player_z / FOV) - wing_extent_x

        top_world = ((CENTER_Y - margin_top) * self.player_z / FOV) - body_extent_y
        bottom_world = ((CENTER_Y - (HEIGHT - 1 - margin_bottom)) * self.player_z / FOV) + body_extent_y

        self.player_x = max(left_world, min(right_world, self.player_x))
        self.player_y = max(bottom_world, min(top_world, self.player_y))

        if self.bullet_cooldown > 0:
            self.bullet_cooldown -= 1

        if self.is_action_held() and self.bullet_cooldown == 0:
            spawn_z = self.player_z + 5.0
            self.bullets.append(
                Bullet(
                    x=self.player_x,
                    y=self.player_y,
                    z=spawn_z,
                    speed=6.5,
                    # Keep screen position fixed while flying deeper.
                    ray_x=self.player_x / spawn_z,
                    ray_y=self.player_y / spawn_z,
                )
            )
            self.bullet_cooldown = 4

    def update_stars(self) -> None:
        for i, star in enumerate(self.stars):
            star.z -= self.forward_speed * star.speed
            if star.z <= 6.0:
                self.stars[i] = self.make_star(260.0)

    def spawn_enemy(self) -> None:
        self.enemy_spawn_timer += 1
        interval = 18 if self.score > 300 else 24
        if self.enemy_spawn_timer < interval:
            return

        self.enemy_spawn_timer = 0
        self.enemies.append(
            Enemy(
                x=random.uniform(-70.0, 70.0),
                y=random.uniform(-70.0, 70.0),
                z=random.uniform(180.0, 240.0),
                size=random.uniform(8.0, 13.0),
                rot=random.uniform(0.0, math.pi * 2.0),
                rot_speed=random.uniform(-0.10, 0.10),
                speed=random.uniform(1.0, 2.1) + self.score * 0.0008,
            )
        )

    def update_enemies(self) -> None:
        survivors: list[Enemy] = []
        for enemy in self.enemies:
            enemy.z -= enemy.speed + self.forward_speed
            enemy.rot += enemy.rot_speed

            # Remove enemies that passed the camera without damaging the player.
            if enemy.z <= 2.0:
                continue

            survivors.append(enemy)

        self.enemies = survivors

    def update_bullets(self) -> None:
        alive: list[Bullet] = []
        for bullet in self.bullets:
            bullet.z += bullet.speed
            bullet.x = bullet.ray_x * bullet.z
            bullet.y = bullet.ray_y * bullet.z
            if bullet.z < 260.0:
                alive.append(bullet)
        self.bullets = alive

    def spawn_enemy_shatter(self, enemy: Enemy) -> None:
        piece_count = 12
        for _ in range(piece_count):
            ang = random.uniform(0.0, math.pi * 2.0)
            elev = random.uniform(-0.9, 0.9)
            speed = random.uniform(0.7, 2.6)
            vx = math.cos(ang) * speed
            vy = math.sin(ang) * speed
            vz = elev * speed + random.uniform(-0.4, 0.5)
            life = random.randint(12, 22)
            self.debris.append(
                Debris(
                    x=enemy.x,
                    y=enemy.y,
                    z=enemy.z,
                    vx=vx,
                    vy=vy,
                    vz=vz,
                    life=life,
                    max_life=life,
                )
            )

    def update_debris(self) -> None:
        alive: list[Debris] = []
        for d in self.debris:
            d.x += d.vx
            d.y += d.vy
            d.z += d.vz - self.forward_speed
            d.vx *= 0.97
            d.vy *= 0.97
            d.vz *= 0.95
            d.life -= 1

            if d.life > 0 and d.z > NEAR_Z:
                alive.append(d)

        self.debris = alive

    def check_collisions(self) -> None:
        enemy_alive = [True] * len(self.enemies)
        bullet_alive = [True] * len(self.bullets)

        for bi, bullet in enumerate(self.bullets):
            for ei, enemy in enumerate(self.enemies):
                if not enemy_alive[ei]:
                    continue

                dz = abs(bullet.z - enemy.z)
                if dz > enemy.size + 3.0:
                    continue

                dx = bullet.x - enemy.x
                dy = bullet.y - enemy.y
                hit_radius = enemy.size + 2.0
                if dx * dx + dy * dy <= hit_radius * hit_radius:
                    bullet_alive[bi] = False
                    enemy_alive[ei] = False
                    self.spawn_enemy_shatter(enemy)
                    self.score += 10
                    break

        remaining_enemies: list[Enemy] = []
        for alive, enemy in zip(enemy_alive, self.enemies):
            if not alive:
                continue

            dz = abs(enemy.z - self.player_z)
            if dz <= enemy.size + self.player_size:
                dx = enemy.x - self.player_x
                dy = enemy.y - self.player_y
                hit_radius = enemy.size + self.player_size
                if dx * dx + dy * dy <= hit_radius * hit_radius:
                    self.hp = max(0, self.hp - 18)
                    self.damage_flash_timer = 6
                    self.spawn_enemy_shatter(enemy)
                    continue

            remaining_enemies.append(enemy)

        self.enemies = remaining_enemies
        self.bullets = [b for i, b in enumerate(self.bullets) if bullet_alive[i]]

    def draw(self) -> None:
        pyxel.cls(pyxel.COLOR_BLACK)

        if self.state == STATE_TITLE:
            self.draw_title()
        elif self.state == STATE_GAME:
            self.draw_game()
        else:
            self.draw_game_over()

    def draw_title(self) -> None:
        pyxel.text(96, 40, "3D SHOOTING", pyxel.COLOR_WHITE)
        pyxel.text(58, 204, "PRESS SPACE TO START", pyxel.COLOR_YELLOW)

        angle = self.frame * 0.05
        self.draw_wire_pyramid(0.0, 0.0, 80.0, 11.0, pyxel.COLOR_WHITE, yaw=angle)

    def draw_game(self) -> None:
        self.draw_stars()

        for enemy in self.enemies:
            self.draw_wire_enemy(enemy)

        for bullet in self.bullets:
            self.draw_wire_bullet(bullet)

        for d in self.debris:
            self.draw_debris(d)

        # Draw the player's ship last so it stays readable in front.
        self.draw_wire_pyramid(
            self.player_x,
            self.player_y,
            self.player_z,
            self.player_size,
            pyxel.COLOR_WHITE,
            yaw=0.0,
        )

        pyxel.rect(0, 0, WIDTH, 12, pyxel.COLOR_NAVY)
        pyxel.text(6, 3, f"HP:{self.hp:03d}", pyxel.COLOR_WHITE)
        pyxel.text(92, 3, f"SCORE:{self.score}", pyxel.COLOR_WHITE)
        pyxel.text(188, 3, f"HIGH:{self.high_score}", pyxel.COLOR_YELLOW)

        if self.damage_flash_timer > 0 and (self.damage_flash_timer % 2 == 0):
            pyxel.rect(0, 0, WIDTH, HEIGHT, pyxel.COLOR_WHITE)

    def draw_game_over(self) -> None:
        pyxel.text(94, 90, "GAME OVER", pyxel.COLOR_RED)
        pyxel.text(90, 116, f"SCORE: {self.score}", pyxel.COLOR_WHITE)
        pyxel.text(82, 132, f"HIGH SCORE: {self.high_score}", pyxel.COLOR_YELLOW)

        if self.new_high_score:
            pyxel.text(70, 152, "NEW HIGH SCORE!", pyxel.COLOR_LIME)

        pyxel.text(62, 198, "PRESS SPACE FOR TITLE", pyxel.COLOR_WHITE)

    def draw_stars(self) -> None:
        for star in self.stars:
            pos = self.project(star.x, star.y, star.z)
            if pos is None:
                continue

            sx, sy = pos
            if sx < 0 or sx >= WIDTH or sy < 12 or sy >= HEIGHT:
                continue

            if star.z < 45:
                color = pyxel.COLOR_WHITE
            elif star.z < 95:
                color = pyxel.COLOR_GRAY
            else:
                color = pyxel.COLOR_DARK_BLUE

            pyxel.pset(int(sx), int(sy), color)

    def draw_wire_enemy(self, enemy: Enemy) -> None:
        corners = []
        for lx, ly in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
            x = lx * enemy.size
            y = ly * enemy.size
            ca = math.cos(enemy.rot)
            sa = math.sin(enemy.rot)
            rx = x * ca - y * sa
            ry = x * sa + y * ca
            corners.append((enemy.x + rx, enemy.y + ry, enemy.z))

        proj = [self.project(x, y, z) for x, y, z in corners]
        if any(p is None for p in proj):
            return

        pts = [(int(p[0]), int(p[1])) for p in proj if p is not None]
        for i in range(4):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % 4]
            pyxel.line(x1, y1, x2, y2, pyxel.COLOR_RED)

    def draw_wire_bullet(self, bullet: Bullet) -> None:
        pos = self.project(bullet.x, bullet.y, bullet.z)
        if pos is None:
            return

        sx, sy = pos
        r = max(1, int(3.0 * FOV / bullet.z))
        pyxel.circb(int(sx), int(sy), r, pyxel.COLOR_YELLOW)

    def draw_debris(self, debris: Debris) -> None:
        p1 = self.project(debris.x, debris.y, debris.z)
        p2 = self.project(
            debris.x + debris.vx * 1.4,
            debris.y + debris.vy * 1.4,
            debris.z + debris.vz * 1.4,
        )
        if p1 is None or p2 is None:
            return

        life_ratio = debris.life / debris.max_life
        color = pyxel.COLOR_RED if life_ratio > 0.45 else pyxel.COLOR_ORANGE
        pyxel.line(int(p1[0]), int(p1[1]), int(p2[0]), int(p2[1]), color)

    def draw_wire_pyramid(
        self,
        x: float,
        y: float,
        z: float,
        size: float,
        color: int,
        yaw: float,
    ) -> None:
        local_vertices = [
            (-size, -size, -size),
            (size, -size, -size),
            (size, size, -size),
            (-size, size, -size),
            (0.0, 0.0, size),
            (-size * 2.0, 0.0, -size * 0.2),
            (size * 2.0, 0.0, -size * 0.2),
        ]

        world_vertices: list[tuple[float, float, float]] = []
        for lx, ly, lz in local_vertices:
            rx, rz = self.rotate_y(lx, lz, yaw)
            world_vertices.append((x + rx, y + ly, z + rz))

        projected = [self.project(vx, vy, vz) for vx, vy, vz in world_vertices]
        if any(p is None for p in projected):
            return

        pts = [(int(p[0]), int(p[1])) for p in projected if p is not None]
        edges = [
            (0, 1),
            (1, 2),
            (2, 3),
            (3, 0),
            (0, 4),
            (1, 4),
            (2, 4),
            (3, 4),
            (0, 5),
            (3, 5),
            (1, 6),
            (2, 6),
            (5, 6),
        ]

        for a, b in edges:
            pyxel.line(pts[a][0], pts[a][1], pts[b][0], pts[b][1], color)


App()
