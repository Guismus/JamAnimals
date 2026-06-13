# Main Game Controller for WildChain: Apex Hunt (Adventure Maps Port)
import pygame
import sys
import os
import json
import math
import random
import sound_gen
from entities import Player, Rabbit, Wolf, Lake, Bridge, Portal, Bush, Burrow, Berry, is_in_impassable_water
from particles import ParticleSystem, draw_circle_alpha, draw_rect_alpha

# Constants
ARENA_WIDTH = 2400
ARENA_HEIGHT = 2400
DAY_NIGHT_DURATION = 30 * 60 # 30 seconds at 60 FPS

class SoundController:
    def __init__(self):
        self.enabled = True
        self.sounds = {}
        # Pre-synthesize sound files if missing
        sound_gen.generate_all_sounds("sounds")
        
        # Load WAV files
        sound_files = ["catch", "dash", "hurt", "alert", "night", "heartbeat"]
        for s in sound_files:
            path = os.path.join("sounds", f"{s}.wav")
            if os.path.exists(path):
                try:
                    self.sounds[s] = pygame.mixer.Sound(path)
                except Exception as e:
                    print(f"Error loading sound {s}: {e}")
                    
        # Heartbeat controls
        self.heartbeat_rate = 0
        self.heartbeat_timer = 0

    def set_enabled(self, val):
        self.enabled = val

    def play(self, name):
        if self.enabled and name in self.sounds:
            self.sounds[name].play()

    def set_heartbeat_rate(self, rate):
        self.heartbeat_rate = rate

    def update(self):
        if not self.enabled or self.heartbeat_rate == 0:
            return
            
        self.heartbeat_timer -= 1
        if self.heartbeat_timer <= 0:
            self.play("heartbeat")
            if self.heartbeat_rate == 1:
                self.heartbeat_timer = 54 # slow
            elif self.heartbeat_rate == 2:
                self.heartbeat_timer = 36 # medium
            elif self.heartbeat_rate == 3:
                self.heartbeat_timer = 18 # fast


class Button:
    def __init__(self, rect, text, bg_color, hover_color, text_color, font_size=20):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.hovered = False
        self.font = pygame.font.SysFont('Arial', font_size, bold=True)

    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def draw(self, surface):
        color = self.hover_color if self.hovered else self.bg_color
        # Draw button
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, (46, 204, 113, 120), self.rect, width=1, border_radius=10)
        
        txt = self.font.render(self.text, True, self.text_color)
        surface.blit(txt, (self.rect.centerx - txt.get_width()//2, self.rect.centery - txt.get_height()//2))

    def handle_event(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(mouse_pos):
                return True
        return False


class GameEngine:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        
        self.screen = pygame.display.set_mode((1024, 768), pygame.RESIZABLE)
        pygame.display.set_caption("WildChain: Apex Hunt")
        self.clock = pygame.time.Clock()
        
        # Audio Controller
        self.sound = SoundController()
        
        # Particles
        self.particles = ParticleSystem()
        
        # Game Objects
        self.player = None
        self.rabbits = []
        self.wolves = []
        self.lakes = []
        self.bridges = []
        self.bushes = []
        self.burrows = []
        self.berries = []
        self.decorations = []
        self.portal = None
        
        # Camera & Shake
        self.camera_x = 0.0
        self.camera_y = 0.0
        self.shake_time = 0
        self.shake_intensity = 0
        
        # Day/Night cycle
        self.cycle_timer = DAY_NIGHT_DURATION
        self.is_night = False
        
        # States & Level System
        self.state = 'menu' # 'menu', 'playing', 'paused', 'gameover', 'victory'
        self.level_index = 0
        self.rabbits_caught = 0
        self.rabbits_needed = 5
        self.total_rabbits_caught = 0
        self.survival_frames = 0
        
        self.LEVEL_CONFIGS = [
            {
                "name": "Level 1: The Bridges Crossing",
                "rabbits_needed": 5,
                "description": "A horizontal river cuts the forest in half. Wolves guard the two bridges.",
                "lakes": [
                    {"x": 1200, "y": 1200, "w": 2400, "h": 220, "shape": "rect", "r": 0}
                ],
                "bridges": [
                    {"x": 600, "y": 1200, "w": 140, "h": 260, "shape": "rect", "r": 0},
                    {"x": 1800, "y": 1200, "w": 140, "h": 260, "shape": "rect", "r": 0}
                ]
            },
            {
                "name": "Level 2: The Sacred Isle",
                "rabbits_needed": 5,
                "description": "A deep circular lake surrounds a central island. Four bridges lead to the center.",
                "lakes": [
                    {"x": 1200, "y": 1200, "w": 0, "h": 0, "shape": "circle", "r": 340}
                ],
                "bridges": [
                    # Central Island
                    {"x": 1200, "y": 1200, "w": 0, "h": 0, "shape": "circle", "r": 120},
                    # Bridges
                    {"x": 1200, "y": 940, "w": 90, "h": 200, "shape": "rect", "r": 0},
                    {"x": 1200, "y": 1460, "w": 90, "h": 200, "shape": "rect", "r": 0},
                    {"x": 940, "y": 1200, "w": 200, "h": 90, "shape": "rect", "r": 0},
                    {"x": 1460, "y": 1200, "w": 200, "h": 90, "shape": "rect", "r": 0}
                ]
            },
            {
                "name": "Level 3: The Canal Labyrinth",
                "rabbits_needed": 5,
                "description": "Multiple streams partition the clearing. Navigate the bridge network to escape.",
                "lakes": [
                    {"x": 1200, "y": 700, "w": 2400, "h": 120, "shape": "rect", "r": 0},
                    {"x": 1200, "y": 1700, "w": 2400, "h": 120, "shape": "rect", "r": 0},
                    {"x": 1200, "y": 1200, "w": 120, "h": 2400, "shape": "rect", "r": 0}
                ],
                "bridges": [
                    {"x": 600, "y": 700, "w": 120, "h": 160, "shape": "rect", "r": 0},
                    {"x": 1800, "y": 700, "w": 120, "h": 160, "shape": "rect", "r": 0},
                    {"x": 600, "y": 1700, "w": 120, "h": 160, "shape": "rect", "r": 0},
                    {"x": 1800, "y": 1700, "w": 120, "h": 160, "shape": "rect", "r": 0},
                    {"x": 1200, "y": 400, "w": 160, "h": 120, "shape": "rect", "r": 0},
                    {"x": 1200, "y": 2000, "w": 160, "h": 120, "shape": "rect", "r": 0},
                    {"x": 1200, "y": 1100, "w": 160, "h": 120, "shape": "rect", "r": 0},
                    {"x": 1200, "y": 1300, "w": 160, "h": 120, "shape": "rect", "r": 0}
                ]
            }
        ]
        
        self.generate_forest_static()
        
        # Fonts
        self.font_title = pygame.font.SysFont('Arial', 54, bold=True)
        self.font_subtitle = pygame.font.SysFont('Arial', 18, bold=True)
        self.font_header = pygame.font.SysFont('Arial', 20, bold=True)
        self.font_body = pygame.font.SysFont('Arial', 14)
        
        # Buttons
        self.setup_buttons()

    def setup_buttons(self):
        # Menu Screen Buttons
        self.play_btn = Button((580, 260, 280, 56), "START ADVENTURE", (244, 107, 45), (255, 125, 65), (255, 255, 255), 20)
        
        # Pause Screen Buttons
        self.resume_btn = Button((362, 300, 300, 50), "RESUME", (46, 204, 113), (39, 174, 96), (255, 255, 255))
        self.quit_btn = Button((362, 370, 300, 50), "QUIT TO MENU", (231, 76, 60), (192, 57, 43), (255, 255, 255))
        
        # GameOver Screen Buttons
        self.restart_btn = Button((362, 530, 300, 50), "RESTART LEVEL", (244, 107, 45), (255, 125, 65), (255, 255, 255))
        self.menu_btn = Button((362, 600, 300, 50), "MAIN MENU", (79, 92, 93), (95, 108, 109), (255, 255, 255))
        
        # Victory Screen Buttons
        self.victory_menu_btn = Button((362, 480, 300, 50), "RETURN TO MENU", (46, 204, 113), (39, 174, 96), (255, 255, 255))

    def generate_forest_static(self):
        # Persistent grass decoration
        self.decorations = []
        for _ in range(300):
            dtype = 'grass' if random.random() < 0.8 else 'rock' if random.random() < 0.7 else 'mushroom'
            self.decorations.append({
                'x': random.uniform(0, ARENA_WIDTH),
                'y': random.uniform(0, ARENA_HEIGHT),
                'type': dtype,
                'size': random.uniform(3.0, 7.0),
                'color': (27, 74, 37) if dtype=='grass' else (74, 85, 77) if dtype=='rock' else (150, 45, 45),
                'rot': random.uniform(0, math.pi * 2)
            })

    def get_random_land_pos(self, border=120):
        """Find a coordinate that does not overlap with impassable water."""
        while True:
            rx = random.uniform(border, ARENA_WIDTH - border)
            ry = random.uniform(border, ARENA_HEIGHT - border)
            if not is_in_impassable_water(rx, ry, self.lakes, self.bridges):
                return rx, ry

    def generate_forest_dynamic(self):
        self.lakes = []
        self.bridges = []
        self.bushes = []
        self.burrows = []
        self.berries = []
        
        # Read configs
        config = self.LEVEL_CONFIGS[self.level_index]
        self.rabbits_needed = config["rabbits_needed"]
        
        # Spawn configured lakes
        for l in config["lakes"]:
            self.lakes.append(Lake(l["x"], l["y"], l["w"], l["h"], l["shape"], l["r"]))
            
        # Spawn configured bridges
        for b in config["bridges"]:
            self.bridges.append(Bridge(b["x"], b["y"], b["w"], b["h"], b["shape"], b["r"]))
            
        # Portal centered
        self.portal = Portal(1200, 1200)
            
        # Spawn bushes on land
        for _ in range(15):
            lx, ly = self.get_random_land_pos()
            self.bushes.append(Bush(lx, ly, random.uniform(28, 40)))
            
        # Spawn burrows on land
        for _ in range(9):
            lx, ly = self.get_random_land_pos()
            self.burrows.append(Burrow(lx, ly))
            
        # Spawn initial berries on land
        for _ in range(8):
            self.spawn_berry()

    def spawn_berry(self):
        lx, ly = self.get_random_land_pos()
        self.berries.append(Berry(lx, ly))

    def spawn_rabbit(self, initial=False):
        if initial:
            while True:
                rx, ry = self.get_random_land_pos()
                if math.hypot(rx - ARENA_WIDTH/2, ry - ARENA_HEIGHT/2) > 250:
                    break
        else:
            # Spawn outside view, retry if stuck in water
            w, h = self.screen.get_size()
            dist = max(w, h) * 0.7
            attempts = 0
            while attempts < 20:
                a = random.uniform(0, math.pi * 2)
                rx = self.player.x + math.cos(a) * dist
                ry = self.player.y + math.sin(a) * dist
                rx = max(50, min(ARENA_WIDTH - 50, rx))
                ry = max(50, min(ARENA_HEIGHT - 50, ry))
                if not is_in_impassable_water(rx, ry, self.lakes, self.bridges):
                    break
                attempts += 1
            if attempts >= 20:
                rx, ry = self.get_random_land_pos()
        self.rabbits.append(Rabbit(rx, ry))

    def spawn_wolf(self, initial=False):
        if initial:
            while True:
                wx, wy = self.get_random_land_pos()
                if math.hypot(wx - ARENA_WIDTH/2, wy - ARENA_HEIGHT/2) > 600:
                    break
        else:
            w, h = self.screen.get_size()
            dist = max(w, h) * 0.8
            attempts = 0
            while attempts < 20:
                a = random.uniform(0, math.pi * 2)
                wx = self.player.x + math.cos(a) * dist
                wy = self.player.y + math.sin(a) * dist
                wx = max(50, min(ARENA_WIDTH - 50, wx))
                wy = max(50, min(ARENA_HEIGHT - 50, wy))
                if not is_in_impassable_water(wx, wy, self.lakes, self.bridges):
                    break
                attempts += 1
            if attempts >= 20:
                wx, wy = self.get_random_land_pos()
        self.wolves.append(Wolf(wx, wy))

    def start_game(self):
        self.level_index = 0
        self.total_rabbits_caught = 0
        self.survival_frames = 0
        self.load_level()
        self.state = 'playing'

    def load_level(self):
        self.sound.play("catch")
        
        self.rabbits.clear()
        self.wolves.clear()
        self.particles.clear()
        
        self.generate_forest_dynamic()
        
        # Ensure spawn coordinate is on land (not in river)
        px, py = self.get_random_land_pos()
        self.player = Player(px, py)
        
        # Spawn Level entities
        for _ in range(12):
            self.spawn_rabbit(True)
        # Increase initial wolf counts in higher maps
        w_count = 3 + self.level_index
        for _ in range(w_count):
            self.spawn_wolf(True)
            
        self.rabbits_caught = 0
        self.cycle_timer = DAY_NIGHT_DURATION
        self.is_night = False

    def next_level(self):
        self.level_index += 1
        if self.level_index < len(self.LEVEL_CONFIGS):
            self.load_level()
            self.sound.play("catch")
            self.trigger_shake(8, 15)
        else:
            # Won the adventure!
            self.state = 'victory'
            self.sound.set_heartbeat_rate(0)
            self.sound.play("night")

    def pause_game(self):
        self.state = 'paused'
        self.sound.set_heartbeat_rate(0)

    def resume_game(self):
        self.sound.play("catch")
        self.state = 'playing'

    def quit_to_menu(self):
        self.sound.play("catch")
        self.state = 'menu'
        self.sound.set_heartbeat_rate(0)

    def game_over(self):
        self.state = 'gameover'
        self.sound.set_heartbeat_rate(0)

    def trigger_shake(self, intensity, frames):
        self.shake_intensity = intensity
        self.shake_time = frames

    # --- MAIN UPDATES ---
    def update(self):
        if self.state != 'playing':
            self.particles.update()
            return

        # Player inputs and update
        self.handle_player_input()
        self.player.update(ARENA_WIDTH, ARENA_HEIGHT, self.bushes, self.lakes, self.bridges, self.particles, self.sound)

        # Hiding in bushes
        for bush in self.bushes:
            if math.hypot(self.player.x - bush.x, self.player.y - bush.y) < bush.radius:
                self.player.is_hidden = True

        # Update rabbits
        for r in list(self.rabbits):
            r.update(ARENA_WIDTH, ARENA_HEIGHT, self.bushes, self.player, self.burrows, self.lakes, self.bridges)
            if r.radius <= 0.0:
                self.rabbits.remove(r)
                self.spawn_rabbit()

        # Update wolves
        closest_wolf_dist = float('inf')
        closest_wolf_state = 'patrol'
        
        for w in self.wolves:
            w.update(ARENA_WIDTH, ARENA_HEIGHT, self.bushes, self.player, self.is_night, self.particles, self.sound, self.lakes, self.bridges)
            d = math.hypot(self.player.x - w.x, self.player.y - w.y)
            if d < closest_wolf_dist:
                closest_wolf_dist = d
                closest_wolf_state = w.state

        # Heartbeat warn
        hr = 0
        if closest_wolf_dist < 120 and closest_wolf_state == 'chase':
            hr = 3
        elif closest_wolf_dist < 220 and closest_wolf_state == 'chase':
            hr = 2
        elif closest_wolf_dist < 320 and (closest_wolf_state == 'chase' or closest_wolf_state == 'cooldown'):
            hr = 1
        self.sound.set_heartbeat_rate(hr)
        self.sound.update()

        # Eat rabbit collision
        for r in list(self.rabbits):
            if r.state != 'escaping' and self.player.collides_with(r):
                self.particles.spawn_eat(r.x, r.y, False)
                self.rabbits.remove(r)
                
                self.player.hunger = min(self.player.max_hunger, self.player.hunger + 35.0)
                self.rabbits_caught += 1
                self.total_rabbits_caught += 1
                
                self.sound.play("catch")
                self.spawn_rabbit()

        # Eat berries
        for b in list(self.berries):
            if math.hypot(self.player.x - b.x, self.player.y - b.y) < (self.player.radius + b.radius):
                self.particles.spawn_eat(b.x, b.y, True)
                self.berries.remove(b)
                
                self.player.hunger = min(self.player.max_hunger, self.player.hunger + 12.0)
                
                self.sound.play("catch")
                self.berries.append(Berry(random.uniform(50, ARENA_WIDTH-50), random.uniform(50, ARENA_HEIGHT-50)))

        # Hurt from wolf
        for w in self.wolves:
            if self.player.collides_with(w):
                if self.player.invuln_frames <= 0:
                    self.player.take_damage(1, self.particles, self.sound)
                    self.trigger_shake(12, 20)
                    if self.player.lives <= 0:
                        self.game_over()

        # Portal Active check
        if self.rabbits_caught >= self.rabbits_needed:
            self.portal.active = True
            
        self.portal.update()
        
        # Step into portal check
        if self.portal.active and math.hypot(self.player.x - self.portal.x, self.player.y - self.portal.y) < (self.player.radius + self.portal.radius):
            self.next_level()

        # Day/Night countdown
        self.cycle_timer -= 1
        if self.cycle_timer <= 0:
            self.cycle_timer = DAY_NIGHT_DURATION
            self.is_night = not self.is_night
            
            if self.is_night:
                self.sound.play("night")
                self.trigger_shake(4, 15)
            else:
                self.sound.play("catch")

        # Spawn fireflies at night
        if self.is_night and random.random() < 0.08:
            w, h = self.screen.get_size()
            self.particles.spawn_fireflies(w, h, self.camera_x, self.camera_y)

        # wolf spawn timer
        self.survival_frames += 1
        if self.survival_frames % 2400 == 0:
            if len(self.wolves) < 9:
                self.spawn_wolf()

        self.particles.update()

    def handle_player_input(self):
        keys = pygame.key.get_pressed()
        move_x = 0
        move_y = 0

        # Keyboard checks
        if keys[pygame.K_w] or keys[pygame.K_UP]: move_y = -1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: move_y = 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: move_x = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: move_x = 1

        # Drag checks
        mouse_down = pygame.mouse.get_pressed()
        if move_x != 0 or move_y != 0:
            length = math.sqrt(move_x*move_x + move_y*move_y)
            self.player.vx = (move_x / length) * self.player.speed
            self.player.vy = (move_y / length) * self.player.speed
        elif mouse_down[0]:
            mx, my = pygame.mouse.get_pos()
            px = self.player.x - self.camera_x
            py = self.player.y - self.camera_y
            dx = mx - px
            dy = my - py
            dist = math.sqrt(dx*dx + dy*dy)
            
            if dist > 15:
                self.player.vx = (dx / dist) * self.player.speed
                self.player.vy = (dy / dist) * self.player.speed
            else:
                self.player.vx = 0.0
                self.player.vy = 0.0
        else:
            self.player.vx *= 0.7
            self.player.vy *= 0.7
            if abs(self.player.vx) < 0.05: self.player.vx = 0
            if abs(self.player.vy) < 0.05: self.player.vy = 0

    # --- RENDERING ---
    def draw(self):
        self.screen.fill((6, 19, 9)) # Floor color
        
        w, h = self.screen.get_size()
        
        # Smooth camera scroll
        if self.player:
            target_cx = self.player.x - w / 2
            target_cy = self.player.y - h / 2
        else:
            target_cx = ARENA_WIDTH / 2 - w / 2
            target_cy = ARENA_HEIGHT / 2 - h / 2
            
        self.camera_x += (target_cx - self.camera_x) * 0.12
        self.camera_y += (target_cy - self.camera_y) * 0.12
        
        # Bounds clamping
        self.camera_x = max(0.0, min(ARENA_WIDTH - w, self.camera_x))
        self.camera_y = max(0.0, min(ARENA_HEIGHT - h, self.camera_y))

        # Shake Offset
        shake_x, shake_y = 0, 0
        if self.shake_time > 0:
            shake_x = random.randint(-self.shake_intensity, self.shake_intensity)
            shake_y = random.randint(-self.shake_intensity, self.shake_intensity)
            self.shake_time -= 1

        # Draw main scene onto a buffered viewport
        world_surf = pygame.Surface((w, h))
        world_surf.fill((6, 19, 9))
        
        # 1. Grid lines and borders
        self.draw_grid(world_surf)
        
        # 2. Grass decorations
        self.draw_decorations(world_surf)
        
        # 3. Lakes (Water barriers)
        for lake in self.lakes:
            lake.draw(world_surf, self.camera_x, self.camera_y)
            
        # 4. Bridges
        for bridge in self.bridges:
            bridge.draw(world_surf, self.camera_x, self.camera_y)
            
        # 5. Burrows
        for burrow in self.burrows:
            burrow.draw(world_surf, self.camera_x, self.camera_y)
            
        # 6. Portal
        if self.portal:
            self.portal.draw(world_surf, self.camera_x, self.camera_y)
            
        # 7. Berries
        for berry in self.berries:
            berry.draw(world_surf, self.camera_x, self.camera_y)
            
        # 8. Rabbits
        for r in self.rabbits:
            r.draw(world_surf, self.camera_x, self.camera_y)
            
        # 9. Player (Fox)
        if self.player:
            self.player.draw(world_surf, self.camera_x, self.camera_y)
        
        # 10. Wolves
        for wolf in self.wolves:
            wolf.draw(world_surf, self.camera_x, self.camera_y)
            
        # 11. Particles
        self.particles.draw(world_surf, self.camera_x, self.camera_y)
        
        # 12. Bushes (drawn on top of animals)
        for bush in self.bushes:
            bush.draw(world_surf, self.camera_x, self.camera_y)

        # 13. Day/Night vignette
        if self.is_night and self.player:
            self.draw_night_vignette(world_surf)

        # Blit buffer onto screen
        self.screen.blit(world_surf, (shake_x, shake_y))

        # 14. UI Overlays
        if self.state == 'playing':
            self.draw_hud()
        elif self.state == 'menu':
            self.draw_menu()
        elif self.state == 'paused':
            self.draw_paused()
        elif self.state == 'gameover':
            self.draw_gameover()
        elif self.state == 'victory':
            self.draw_victory()

        pygame.display.flip()

    def draw_grid(self, surface):
        x_min = int(-self.camera_x)
        y_min = int(-self.camera_y)
        x_max = int(ARENA_WIDTH - self.camera_x)
        y_max = int(ARENA_HEIGHT - self.camera_y)
        pygame.draw.rect(surface, (3, 11, 5), (x_min, y_min, ARENA_WIDTH, ARENA_HEIGHT), 4)
        
        step = 200
        for x in range(0, ARENA_WIDTH + 1, step):
            pygame.draw.line(surface, (15, 30, 20), (x - int(self.camera_x), y_min), (x - int(self.camera_x), y_max), 1)
        for y in range(0, ARENA_HEIGHT + 1, step):
            pygame.draw.line(surface, (15, 30, 20), (x_min, y - int(self.camera_y)), (x_max, y - int(self.camera_y)), 1)

    def draw_decorations(self, surface):
        w, h = self.screen.get_size()
        margin = 50
        for dec in self.decorations:
            if (self.camera_x - margin <= dec['x'] <= self.camera_x + w + margin and
                self.camera_y - margin <= dec['y'] <= self.camera_y + h + margin):
                
                dx = int(dec['x'] - self.camera_x)
                dy = int(dec['y'] - self.camera_y)
                
                if dec['type'] == 'grass':
                    pygame.draw.line(surface, dec['color'], (dx, dy), (dx - 2, dy - int(dec['size']*2)), 2)
                    pygame.draw.line(surface, dec['color'], (dx, dy), (dx + 2, dy - int(dec['size']*1.5)), 1)
                elif dec['type'] == 'rock':
                    pygame.draw.circle(surface, dec['color'], (dx, dy), int(dec['size']))
                elif dec['type'] == 'mushroom':
                    pygame.draw.rect(surface, (219, 204, 160), (dx - 1, dy - int(dec['size']), 2, int(dec['size'])))
                    pygame.draw.circle(surface, dec['color'], (dx, dy - int(dec['size'])), int(dec['size'] * 1.2))

    def draw_night_vignette(self, surface):
        w, h = self.screen.get_size()
        light_mask = pygame.Surface((w, h))
        light_mask.fill((10, 25, 12)) # Dark ambient
        
        px = self.player.x - self.camera_x
        py = self.player.y - self.camera_y
        
        light_radius = 140 if self.player.is_hidden else 150 if self.player.lives <= 1 else 195
        
        # Concentric circles for smooth gradient spotlight
        for r in range(light_radius, 0, -3):
            t = r / light_radius
            col_r = int(10 + (255 - 10) * (1 - t))
            col_g = int(25 + (255 - 25) * (1 - t))
            col_b = int(12 + (255 - 12) * (1 - t))
            pygame.draw.circle(light_mask, (col_r, col_g, col_b), (int(px), int(py)), r)
            
        surface.blit(light_mask, (0, 0), special_flags=pygame.BLEND_MULT)

    # --- HUD ---
    def draw_hud(self):
        w, h = self.screen.get_size()
        config = self.LEVEL_CONFIGS[self.level_index]
        
        # 1. Hunger bar
        hud_bg = pygame.Surface((280, 50), pygame.SRCALPHA)
        hud_bg.fill((4, 12, 6, 200))
        pygame.draw.rect(hud_bg, (46, 204, 113, 50), (0, 0, 280, 50), border_radius=10, width=1)
        
        pct = max(0.0, min(100.0, self.player.hunger))
        color = (255, 71, 87) if pct < 25 else (244, 107, 45)
        lbl = self.font_subtitle.render("HUNGER", True, color)
        
        # Text vertical centering
        lbl_x = 16
        lbl_y = (50 - lbl.get_height()) // 2
        hud_bg.blit(lbl, (lbl_x, lbl_y))
        
        # Bar geometry inside container
        bar_x = lbl_x + lbl.get_width() + 12
        bar_y = (50 - 12) // 2
        bar_w = 280 - bar_x - 16
        bar_h = 12
        
        pygame.draw.rect(hud_bg, (30, 45, 35), (bar_x, bar_y, bar_w, bar_h), border_radius=6)
        fill_w = int(bar_w * (pct / 100.0))
        if fill_w > 0:
            pygame.draw.rect(hud_bg, color, (bar_x, bar_y, fill_w, bar_h), border_radius=6)
            
        self.screen.blit(hud_bg, (20, 20))
        
        # 2. Day/Night timer
        cycle_bg = pygame.Surface((140, 42), pygame.SRCALPHA)
        cycle_bg.fill((4, 12, 6, 200))
        pygame.draw.rect(cycle_bg, (46, 204, 113, 50), (0, 0, 140, 42), border_radius=8, width=1)
        
        cycle_lbl = "NIGHT" if self.is_night else "DAY"
        cycle_col = (155, 89, 182) if self.is_night else (241, 196, 15)
        txt = self.font_header.render(f"{cycle_lbl} {math.ceil(self.cycle_timer/60)}s", True, cycle_col)
        
        # Center text inside cycle_bg
        txt_x = (140 - txt.get_width()) // 2
        txt_y = (42 - txt.get_height()) // 2
        cycle_bg.blit(txt, (txt_x, txt_y))
        
        self.screen.blit(cycle_bg, (w//2 - 70, 20))

        # 3. Objective & Level stats top right (No scores)
        stats_bg = pygame.Surface((280, 64), pygame.SRCALPHA)
        stats_bg.fill((4, 12, 6, 200))
        pygame.draw.rect(stats_bg, (46, 204, 113, 50), (0, 0, 280, 64), border_radius=10, width=1)
        
        level_lbl = self.font_subtitle.render(config["name"], True, (46, 204, 113))
        # Left margin 16px, vertically centered in top half (height 32)
        level_lbl_y = (32 - level_lbl.get_height()) // 2
        stats_bg.blit(level_lbl, (16, level_lbl_y))
        
        if self.rabbits_caught >= self.rabbits_needed:
            # Active escape prompt
            obj_txt = self.font_header.render("PORTAL OPEN! RUN TO CENTER", True, (241, 196, 15))
        else:
            obj_txt = self.font_body.render(f"Rabbits eaten: {self.rabbits_caught} / {self.rabbits_needed}", True, (255, 255, 255))
            
        # Left margin 16px, vertically centered in bottom half (y=32 to y=64)
        obj_txt_y = 32 + (32 - obj_txt.get_height()) // 2
        stats_bg.blit(obj_txt, (16, obj_txt_y))
        
        self.screen.blit(stats_bg, (w - 300, 20))

        # 4. Lives bottom left
        lives_bg = pygame.Surface((150, 46), pygame.SRCALPHA)
        lives_bg.fill((4, 12, 6, 200))
        pygame.draw.rect(lives_bg, (46, 204, 113, 50), (0, 0, 150, 46), border_radius=10, width=1)
        
        # Center hearts in lives_bg
        cx = 150 // 2
        cy = 46 // 2
        for i in range(self.player.max_lives):
            hx = cx - ((self.player.max_lives - 1) * 28) // 2 + i * 28
            hy = cy
            active = i < self.player.lives
            col = (255, 71, 87) if active else (40, 55, 45)
            pygame.draw.circle(lives_bg, col, (hx - 5, hy - 4), 6)
            pygame.draw.circle(lives_bg, col, (hx + 5, hy - 4), 6)
            pygame.draw.polygon(lives_bg, col, [(hx - 11, hy - 2), (hx + 11, hy - 2), (hx, hy + 10)])
            
        self.screen.blit(lives_bg, (20, h - 66))

        # 5. Dash Cooldown bottom right
        dash_bg = pygame.Surface((180, 46), pygame.SRCALPHA)
        dash_bg.fill((4, 12, 6, 200))
        pygame.draw.rect(dash_bg, (46, 204, 113, 50), (0, 0, 180, 46), border_radius=10, width=1)
        
        dash_lbl = self.font_body.render("DASH (SPACE)", True, (143, 168, 150))
        # Horizontal margin: 12px. Vertical margin: top-aligned
        dash_lbl_x = 12
        dash_lbl_y = 6
        dash_bg.blit(dash_lbl, (dash_lbl_x, dash_lbl_y))
        
        dash_pct = 1.0 - (self.player.dash_cooldown / 90.0) if self.player.dash_cooldown > 0 else 1.0
        dash_fill_w = int(156 * dash_pct)
        # Bar bottom margin: 8px. Height: 6px.
        bar_y = 46 - 8 - 6
        pygame.draw.rect(dash_bg, (30, 45, 35), (12, bar_y, 156, 6), border_radius=3)
        
        dash_col = (46, 204, 113) if dash_pct == 1.0 and self.player.hunger >= 15 else (92, 115, 98)
        if dash_fill_w > 0:
            pygame.draw.rect(dash_bg, dash_col, (12, bar_y, dash_fill_w, 6), border_radius=3)
            
        self.screen.blit(dash_bg, (w - 200, h - 66))

        # 6. Portal Off-Screen Indicator
        if self.portal and self.portal.active:
            px = self.portal.x - self.camera_x
            py = self.portal.y - self.camera_y
            
            margin = 40
            if px < margin or px > w - margin or py < margin or py > h - margin:
                cx_scr = w / 2
                cy_scr = h / 2
                dx = px - cx_scr
                dy = py - cy_scr
                
                t = 1000.0
                limit_x = w / 2 - margin
                limit_y = h / 2 - margin
                
                if dx != 0:
                    tx = limit_x / abs(dx)
                    if tx < t: t = tx
                if dy != 0:
                    ty = limit_y / abs(dy)
                    if ty < t: t = ty
                    
                mx = cx_scr + t * dx
                my = cy_scr + t * dy
                
                # Collision avoidance with HUD elements
                # Bottom-Right (Dash card)
                if mx > w - 210 and my > h - 76:
                    if (w - mx) < (h - my):
                        mx = w - 220
                    else:
                        my = h - 86
                # Bottom-Left (Lives card)
                elif mx < 180 and my > h - 76:
                    if mx < (h - my):
                        mx = 190
                    else:
                        my = h - 86
                # Top-Right (Objective card)
                elif mx > w - 310 and my < 94:
                    if (w - mx) < my:
                        mx = w - 320
                    else:
                        my = 104
                # Top-Left (Hunger card)
                elif mx < 310 and my < 80:
                    if mx < my:
                        mx = 320
                    else:
                        my = 90
                # Top-Center (Timer card)
                elif w//2 - 90 < mx < w//2 + 90 and my < 72:
                    my = 82
                
                # Normalize direction
                dist = math.hypot(dx, dy)
                if dist > 0:
                    ux = dx / dist
                    uy = dy / dist
                else:
                    ux, uy = 0, -1
                    
                # Pulsing size
                pulse = math.sin(pygame.time.get_ticks() * 0.01) * 3
                radius = 16 + int(pulse)
                
                # Draw marker background
                marker_surf = pygame.Surface((radius * 2 + 10, radius * 2 + 10), pygame.SRCALPHA)
                mcx = marker_surf.get_width() // 2
                mcy = marker_surf.get_height() // 2
                
                # Outer glowing circle
                pygame.draw.circle(marker_surf, (46, 204, 113, 80), (mcx, mcy), radius + 4)
                # Inner solid circle
                pygame.draw.circle(marker_surf, (6, 20, 10, 220), (mcx, mcy), radius)
                pygame.draw.circle(marker_surf, (46, 204, 113), (mcx, mcy), radius, width=2)
                
                # Draw arrow pointing to portal inside marker_surf
                tx_arrow = mcx + ux * 8
                ty_arrow = mcy + uy * 8
                bx_arrow = mcx - ux * 6
                by_arrow = mcy - uy * 6
                nx = -uy
                ny = ux
                
                p1 = (tx_arrow, ty_arrow)
                p2 = (bx_arrow + nx * 5, by_arrow + ny * 5)
                p3 = (bx_arrow - nx * 5, by_arrow - ny * 5)
                
                pygame.draw.polygon(marker_surf, (241, 196, 15), [p1, p2, p3])
                
                # Blit marker
                self.screen.blit(marker_surf, (int(mx - mcx), int(my - mcy)))
                
                # Text distance indicator
                dist_m = int(math.hypot(self.player.x - self.portal.x, self.player.y - self.portal.y) / 10)
                txt = self.font_body.render(f"{dist_m}m", True, (255, 255, 255))
                
                # Place text below or above the marker depending on screen hemisphere
                tx_x = int(mx - txt.get_width() // 2)
                tx_y = int(my - radius - 18 if my > h // 2 else my + radius + 6)
                self.screen.blit(txt, (tx_x, tx_y))

    def draw_menu(self):
        w, h = self.screen.get_size()
        bg = pygame.Surface((w, h), pygame.SRCALPHA)
        bg.fill((2, 8, 4, 210))
        self.screen.blit(bg, (0, 0))

        # Main glass panel
        panel = pygame.Surface((900, 600), pygame.SRCALPHA)
        panel.fill((6, 20, 10, 195))
        pygame.draw.rect(panel, (46, 204, 113, 40), (0, 0, 900, 600), border_radius=24, width=1)
        self.screen.blit(panel, (w//2 - 450, h//2 - 300))

        # Game Titles
        title_y = h//2 - 260
        txt_title = self.font_title.render("WILDCHAIN", True, (244, 107, 45))
        self.screen.blit(txt_title, (w//2 - txt_title.get_width()//2, title_y))
        
        txt_sub = self.font_subtitle.render("APEX HUNT & ESCAPE", True, (143, 168, 150))
        self.screen.blit(txt_sub, (w//2 - txt_sub.get_width()//2, title_y + 60))

        badge_y = title_y + 90
        badge_txt = self.font_body.render("Micro Jam 059  |  Theme: Animals  |  Prerequisite: Predator & Prey", True, (46, 204, 113))
        self.screen.blit(badge_txt, (w//2 - badge_txt.get_width()//2, badge_y))

        # Left Column: How to play
        left_x = w//2 - 410
        left_y = badge_y + 40
        card_surf = pygame.Surface((400, 320), pygame.SRCALPHA)
        pygame.draw.rect(card_surf, (0, 0, 0, 105), (0, 0, 400, 320), border_radius=16)
        pygame.draw.rect(card_surf, (46, 204, 113, 60), (0, 0, 400, 320), width=1, border_radius=16)
        self.screen.blit(card_surf, (left_x, left_y))
        
        lbl_inst = self.font_header.render("HOW TO PLAY", True, (46, 204, 113))
        self.screen.blit(lbl_inst, (left_x + 20, left_y + 20))
        
        inst_y = left_y + 54
        instructions = [
            "You are a Fox. You are BOTH predator and prey!",
            "",
            "• HUNT: Catch Rabbits to restore energy (Hunger meter).",
            "• WATERS: Lakes & rivers block you. Slide along shorelines.",
            "• BRIDGES: Use walkable wooden structures to cross waters.",
            "• ESCAPE: Catch 5 Rabbits to open the central Portal ring.",
            "",
            "CONTROLS:",
            "  - Keyboard: W, A, S, D or ARROWS to move.",
            "  - Sprint/Dash: SPACE (costs hunger, 1.5s cooldown).",
            "  - Mouse: Click and Drag to steer. Right-Click to dash."
        ]
        for inst in instructions:
            t = self.font_body.render(inst, True, (200, 215, 205) if "•" in inst else (143, 168, 150))
            self.screen.blit(t, (left_x + 20, inst_y))
            inst_y += 22

        # Right Column: Adventure levels list
        right_x = w//2 + 30
        right_y = badge_y + 40
        
        # Audio setting card
        audio_card = pygame.Surface((380, 60), pygame.SRCALPHA)
        pygame.draw.rect(audio_card, (0, 0, 0, 105), (0, 0, 380, 60), border_radius=12)
        pygame.draw.rect(audio_card, (46, 204, 113, 40), (0, 0, 380, 60), width=1, border_radius=12)
        self.screen.blit(audio_card, (right_x, right_y))
        
        audio_lbl = self.font_body.render("Synthesized Sound FX:", True, (200, 210, 202))
        self.screen.blit(audio_lbl, (right_x + 20, right_y + 20))
        
        audio_state = "ENABLED" if self.sound.enabled else "DISABLED"
        audio_col = (46, 204, 113) if self.sound.enabled else (231, 76, 60)
        audio_status = self.font_header.render(audio_state, True, audio_col)
        self.screen.blit(audio_status, (right_x + 240, right_y + 18))

        # Start Button
        self.play_btn.rect.topleft = (right_x + 50, right_y + 80)
        self.play_btn.draw(self.screen)

        # Levels Progress Card (Replaced Leaderboard)
        lead_y = right_y + 155
        level_card = pygame.Surface((380, 165), pygame.SRCALPHA)
        pygame.draw.rect(level_card, (0, 0, 0, 105), (0, 0, 380, 165), border_radius=16)
        pygame.draw.rect(level_card, (46, 204, 113, 40), (0, 0, 380, 165), width=1, border_radius=16)
        self.screen.blit(level_card, (right_x, lead_y))
        
        lead_lbl = self.font_subtitle.render("ADVENTURE MAPS", True, (241, 196, 15))
        self.screen.blit(lead_lbl, (right_x + 105, lead_y + 12))
        
        list_y = lead_y + 42
        for i, cfg in enumerate(self.LEVEL_CONFIGS):
            col = (46, 204, 113) if i == 0 else (200, 210, 202)
            lbl = self.font_body.render(f"Map {i+1}: {cfg['name']}", True, col)
            self.screen.blit(lbl, (right_x + 20, list_y))
            list_y += 32

        # Footer
        footer = self.font_body.render("Created for Micro Jam 059  •  Sound synthesized locally  •  2026", True, (90, 110, 95))
        self.screen.blit(footer, (w//2 - footer.get_width()//2, h//2 + 270))

    def draw_paused(self):
        w, h = self.screen.get_size()
        bg = pygame.Surface((w, h), pygame.SRCALPHA)
        bg.fill((2, 8, 4, 180))
        self.screen.blit(bg, (0, 0))

        # Panel
        panel = pygame.Surface((400, 280), pygame.SRCALPHA)
        panel.fill((6, 20, 10, 200))
        pygame.draw.rect(panel, (46, 204, 113, 50), (0, 0, 400, 280), border_radius=20, width=1)
        self.screen.blit(panel, (w//2 - 200, h//2 - 140))

        txt = self.font_title.render("PAUSED", True, (255, 255, 255))
        self.screen.blit(txt, (w//2 - txt.get_width()//2, h//2 - 110))

        self.resume_btn.rect.topleft = (w//2 - 150, h//2 - 20)
        self.quit_btn.rect.topleft = (w//2 - 150, h//2 + 50)
        
        self.resume_btn.draw(self.screen)
        self.quit_btn.draw(self.screen)

    def draw_gameover(self):
        w, h = self.screen.get_size()
        bg = pygame.Surface((w, h), pygame.SRCALPHA)
        bg.fill((5, 1, 1, 220))
        self.screen.blit(bg, (0, 0))

        # Panel
        panel = pygame.Surface((500, 320), pygame.SRCALPHA)
        panel.fill((20, 6, 6, 200))
        pygame.draw.rect(panel, (231, 76, 60, 50), (0, 0, 500, 320), border_radius=20, width=1)
        self.screen.blit(panel, (w//2 - 250, h//2 - 160))

        # Title
        title_y = h//2 - 130
        txt = self.font_title.render("DEFEATED", True, (231, 76, 60))
        self.screen.blit(txt, (w//2 - txt.get_width()//2, title_y))
        
        sub = self.font_subtitle.render("The food chain claims another victim.", True, (143, 168, 150))
        self.screen.blit(sub, (w//2 - sub.get_width()//2, title_y + 60))

        # Bottom Actions
        self.restart_btn.rect.topleft = (w//2 - 150, h//2 + 5)
        self.menu_btn.rect.topleft = (w//2 - 150, h//2 + 70)
        
        self.restart_btn.draw(self.screen)
        self.menu_btn.draw(self.screen)

    def draw_victory(self):
        w, h = self.screen.get_size()
        bg = pygame.Surface((w, h), pygame.SRCALPHA)
        bg.fill((2, 8, 4, 230))
        self.screen.blit(bg, (0, 0))

        # Panel
        panel = pygame.Surface((540, 320), pygame.SRCALPHA)
        panel.fill((6, 20, 10, 200))
        pygame.draw.rect(panel, (241, 196, 15, 60), (0, 0, 540, 320), border_radius=24, width=1)
        self.screen.blit(panel, (w//2 - 270, h//2 - 160))

        # Golden Titles
        title_y = h//2 - 130
        txt = self.font_title.render("VICTORY!", True, (241, 196, 15))
        self.screen.blit(txt, (w//2 - txt.get_width()//2, title_y))
        
        sub = self.font_subtitle.render("You successfully escaped the forest canals!", True, (46, 204, 113))
        self.screen.blit(sub, (w//2 - sub.get_width()//2, title_y + 60))

        # Quote
        quote = self.font_body.render("You are the master of predator and prey.", True, (143, 168, 150))
        self.screen.blit(quote, (w//2 - quote.get_width()//2, h//2 + 10))

        # Button
        self.victory_menu_btn.rect.topleft = (w//2 - 150, h//2 + 50)
        self.victory_menu_btn.draw(self.screen)

    # --- MAIN ENGINE RUN ---
    def run(self):
        while True:
            mouse_pos = pygame.mouse.get_pos()
            
            # Button states update
            if self.state == 'menu':
                self.play_btn.update(mouse_pos)
            elif self.state == 'paused':
                self.resume_btn.update(mouse_pos)
                self.quit_btn.update(mouse_pos)
            elif self.state == 'gameover':
                self.restart_btn.update(mouse_pos)
                self.menu_btn.update(mouse_pos)
            elif self.state == 'victory':
                self.victory_menu_btn.update(mouse_pos)

            # Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                    
                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE and self.state == 'playing':
                        self.pause_game()
                    elif event.key == pygame.K_SPACE and self.state == 'playing':
                        self.player.trigger_dash(self.particles, self.sound)
                                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 3 and self.state == 'playing':
                        self.player.trigger_dash(self.particles, self.sound)
                        
                    if self.state == 'menu' and event.button == 1:
                        w, h = self.screen.get_size()
                        toggle_rect = pygame.Rect(w//2 + 30, h//2 - 130 + 40, 380, 60)
                        if toggle_rect.collidepoint(mouse_pos):
                            self.sound.set_enabled(not self.sound.enabled)
                            self.sound.play("catch")

                # Handle clicks on buttons
                if self.state == 'menu':
                    if self.play_btn.handle_event(event, mouse_pos):
                        self.start_game()
                elif self.state == 'paused':
                    if self.resume_btn.handle_event(event, mouse_pos):
                        self.resume_game()
                    elif self.quit_btn.handle_event(event, mouse_pos):
                        self.quit_to_menu()
                elif self.state == 'gameover':
                    if self.restart_btn.handle_event(event, mouse_pos):
                        self.load_level()
                        self.state = 'playing'
                    elif self.menu_btn.handle_event(event, mouse_pos):
                        self.quit_to_menu()
                elif self.state == 'victory':
                    if self.victory_menu_btn.handle_event(event, mouse_pos):
                        self.quit_to_menu()

            # Physics and render draws
            self.update()
            self.draw()
            self.clock.tick(60)

if __name__ == "__main__":
    game = GameEngine()
    game.run()
