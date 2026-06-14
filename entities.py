# Entities module for WildChain: Apex Hunt (Pygame Port)
import pygame
import math
import random

def is_in_impassable_water(x, y, lakes, bridges):
    """Check if coordinate (x, y) is in water and NOT on a bridge."""
    for b in bridges:
        if b.contains(x, y):
            return False
    for l in lakes:
        if l.contains(x, y):
            return True
    return False


class Entity:
    def __init__(self, x, y, radius, color):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.vx = 0.0
        self.vy = 0.0
        self.angle = 0.0
        self.speed = 0.0

    def collides_with(self, other):
        dx = self.x - other.x
        dy = self.y - other.y
        dist = math.sqrt(dx * dx + dy * dy)
        return dist < (self.radius + other.radius)

    def update(self, arena_w, arena_h, obstacles, lakes, bridges):
        # Move X with water sliding
        self.x += self.vx
        if is_in_impassable_water(self.x, self.y, lakes, bridges):
            self.x -= self.vx
            self.vx = 0.0
            
        # Move Y with water sliding
        self.y += self.vy
        if is_in_impassable_water(self.x, self.y, lakes, bridges):
            self.y -= self.vy
            self.vy = 0.0

        # Boundary checks
        if self.x < self.radius:
            self.x = self.radius
            self.vx *= -0.5
        if self.x > arena_w - self.radius:
            self.x = arena_w - self.radius
            self.vx *= -0.5
        if self.y < self.radius:
            self.y = self.radius
            self.vy *= -0.5
        if self.y > arena_h - self.radius:
            self.y = arena_h - self.radius
            self.vy *= -0.5

    def draw(self, surface, camera_x, camera_y):
        # Fallback circle
        draw_x = int(self.x - camera_x)
        draw_y = int(self.y - camera_y)
        pygame.draw.circle(surface, self.color, (draw_x, draw_y), int(self.radius))


# 1. PLAYER (FOX)
class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 16, (244, 107, 45))
        self.base_speed = 3.6
        self.speed = self.base_speed
        self.lives = 3
        self.max_lives = 3
        
        # Hunger
        self.hunger = 100.0
        self.max_hunger = 100.0
        
        # Dash
        self.dash_cooldown = 0
        self.dash_duration = 0
        self.is_dashing = False
        
        # States
        self.invuln_frames = 0
        self.is_hidden = False
        self.in_mud = False
        
        # Wiggle cycle
        self.anim_cycle = 0.0

    def trigger_dash(self, particles, sound_controller):
        if self.dash_cooldown > 0 or self.hunger < 15:
            return
        self.is_dashing = True
        self.dash_duration = 15
        self.dash_cooldown = 90
        self.hunger -= 12.0
        
        for _ in range(5):
            particles.spawn_dust(self.x, self.y)
        sound_controller.play("dash")

    def update(self, arena_w, arena_h, obstacles, lakes, bridges, particles, sound_controller):
        # Hunger decay
        if self.hunger > 0:
            self.hunger -= 0.16 if self.is_dashing else 0.044
        else:
            self.hunger = 0.0
            if random.random() < 0.003:
                self.take_damage(1, particles, sound_controller)

        # Dash and Mud speed calculations
        if self.is_dashing:
            self.speed = self.base_speed * 2.2
            self.dash_duration -= 1
            if self.dash_duration <= 0:
                self.is_dashing = False
        else:
            self.speed = self.base_speed * 0.45 if self.in_mud else self.base_speed

        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
        if self.invuln_frames > 0:
            self.invuln_frames -= 1

        if self.vx != 0.0 or self.vy != 0.0:
            target_angle = math.atan2(self.vy, self.vx)
            diff = target_angle - self.angle
            while diff < -math.pi: diff += math.pi * 2
            while diff > math.pi: diff -= math.pi * 2
            self.angle += diff * 0.25
            
            self.anim_cycle += 0.35 if self.is_dashing else 0.18
            
            # Spawn trail particles
            if random.random() < 0.22:
                if self.in_mud:
                    particles.spawn_splash(self.x, self.y)
                else:
                    particles.spawn_dust(self.x, self.y)

        # Reset states
        self.in_mud = False
        self.is_hidden = False

        # Delegate single-step movement to base class
        super().update(arena_w, arena_h, obstacles, lakes, bridges)

    def take_damage(self, amt, particles, sound_controller):
        if self.invuln_frames > 0:
            return
        self.lives -= amt
        self.invuln_frames = 60
        particles.spawn_bite(self.x, self.y)
        sound_controller.play("hurt")

    def draw(self, surface, camera_x, camera_y):
        # Invulnerable flash effect
        if self.invuln_frames > 0 and (self.invuln_frames // 4) % 2 == 0:
            return

        # Render onto local surface for smooth rotation
        local_w, local_h = 80, 80
        local_surf = pygame.Surface((local_w, local_h), pygame.SRCALPHA)
        cx, cy = local_w // 2, local_h // 2

        # 1. Wiggling Tail
        tail_wiggle = math.sin(self.anim_cycle) * 0.35
        tail_angle = math.pi + tail_wiggle
        tip_x = cx - 10 + math.cos(tail_angle) * 20
        tip_y = cy + math.sin(tail_angle) * 20
        
        pts = [
            (cx - 8, cy - 3),
            (cx - 16 + math.cos(tail_angle - 0.2) * 10, cy + math.sin(tail_angle - 0.2) * 10),
            (tip_x, tip_y),
            (cx - 16 + math.cos(tail_angle + 0.2) * 10, cy + math.sin(tail_angle + 0.2) * 10),
            (cx - 8, cy + 3)
        ]
        pygame.draw.polygon(local_surf, (244, 107, 45), pts)
        
        # White tip
        white_pts = [
            (cx - 16 + math.cos(tail_angle - 0.15) * 14, cy + math.sin(tail_angle - 0.15) * 14),
            (tip_x, tip_y),
            (cx - 16 + math.cos(tail_angle + 0.15) * 14, cy + math.sin(tail_angle + 0.15) * 14)
        ]
        pygame.draw.polygon(local_surf, (255, 255, 255), white_pts)

        # 2. Paws
        paws_color = (30, 39, 44)
        leg_offset = int(math.sin(self.anim_cycle) * 5)
        # Back left
        pygame.draw.rect(local_surf, paws_color, (cx - 6, cy - 12 + leg_offset, 3, 5))
        # Back right
        pygame.draw.rect(local_surf, paws_color, (cx + 4, cy - 12 - leg_offset, 3, 5))
        # Front left
        pygame.draw.rect(local_surf, paws_color, (cx - 6, cy + 7 - leg_offset, 3, 5))
        # Front right
        pygame.draw.rect(local_surf, paws_color, (cx + 4, cy + 7 + leg_offset, 3, 5))

        # 3. Main Body
        pygame.draw.ellipse(local_surf, (244, 107, 45), (cx - 15, cy - 10, 30, 20))
        # White chest
        pygame.draw.ellipse(local_surf, (255, 255, 255), (cx - 1, cy - 5, 12, 10))

        # 4. Head (facing right)
        head_pts = [
            (cx + 10, cy - 8),
            (cx + 20, cy - 2),
            (cx + 20, cy + 2),
            (cx + 10, cy + 8)
        ]
        pygame.draw.polygon(local_surf, (244, 107, 45), head_pts)
        
        # Cheeks
        pygame.draw.ellipse(local_surf, (255, 255, 255), (cx + 11, cy - 6, 4, 12))
        
        # Nose tip
        pygame.draw.circle(local_surf, (17, 17, 17), (cx + 20, cy), 2)

        # Ears (backwards/upwards)
        pygame.draw.polygon(local_surf, (44, 62, 80), [(cx + 10, cy - 6), (cx + 4, cy - 12), (cx + 8, cy - 4)])
        pygame.draw.polygon(local_surf, (255, 168, 114), [(cx + 9, cy - 5.5), (cx + 5, cy - 10), (cx + 8, cy - 4.5)])
        
        pygame.draw.polygon(local_surf, (44, 62, 80), [(cx + 10, cy + 6), (cx + 4, cy + 12), (cx + 8, cy + 4)])
        pygame.draw.polygon(local_surf, (255, 168, 114), [(cx + 9, cy + 5.5), (cx + 5, cy + 10), (cx + 8, cy + 4.5)])

        # Eyes
        pygame.draw.circle(local_surf, (17, 17, 17), (cx + 14, cy - 3), 1)
        pygame.draw.circle(local_surf, (17, 17, 17), (cx + 14, cy + 3), 1)
        
        if self.is_dashing:
            pygame.draw.circle(local_surf, (255, 255, 255), (cx + 14, cy - 3), 1)
            pygame.draw.circle(local_surf, (255, 255, 255), (cx + 14, cy + 3), 1)

        # Rotate local surface
        deg = -math.degrees(self.angle)
        rotated_surf = pygame.transform.rotate(local_surf, deg)
        
        if self.is_hidden:
            rotated_surf.set_alpha(110)
        else:
            rotated_surf.set_alpha(255)
            
        new_rect = rotated_surf.get_rect(center=(int(self.x - camera_x), int(self.y - camera_y)))
        surface.blit(rotated_surf, new_rect.topleft)


# 2. PREY (RABBIT)
class Rabbit(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 10, (189, 195, 197))
        self.speed = 1.95
        self.state = 'idle'
        self.wander_timer = 0
        self.wander_vx = 0.0
        self.wander_vy = 0.0
        self.escape_burrow = None
        self.anim_cycle = random.uniform(0.0, 100.0)

    def update(self, arena_w, arena_h, obstacles, player, burrows, lakes, bridges):
        dist_to_player = math.hypot(self.x - player.x, self.y - player.y)

        # Flee triggers if player is close and NOT hidden
        if dist_to_player < 150 and not player.is_hidden:
            self.state = 'fleeing'

        if self.state == 'idle':
            self.speed = 0.8
            self.wander_timer -= 1
            if self.wander_timer <= 0:
                self.wander_timer = random.randint(60, 180)
                if random.random() < 0.5:
                    angle = random.uniform(0, math.pi * 2)
                    self.wander_vx = math.cos(angle) * self.speed
                    self.wander_vy = math.sin(angle) * self.speed
                else:
                    self.wander_vx = 0.0
                    self.wander_vy = 0.0
            self.vx = self.wander_vx
            self.vy = self.wander_vy
        elif self.state == 'fleeing':
            self.speed = 2.45
            
            # Find closest burrow
            closest_burrow = None
            min_dist = float('inf')
            for burrow in burrows:
                d = math.hypot(self.x - burrow.x, self.y - burrow.y)
                if d < min_dist:
                    min_dist = d
                    closest_burrow = burrow

            if closest_burrow and min_dist < 120:
                angle_to_burrow = math.atan2(closest_burrow.y - self.y, closest_burrow.x - self.x)
                self.vx = math.cos(angle_to_burrow) * self.speed
                self.vy = math.sin(angle_to_burrow) * self.speed

                if min_dist < 12:
                    self.state = 'escaping'
                    self.escape_burrow = closest_burrow
            else:
                angle_away = math.atan2(self.y - player.y, self.x - player.x)
                self.vx = math.cos(angle_away) * self.speed
                self.vy = math.sin(angle_away) * self.speed
        elif self.state == 'escaping':
            self.vx = (self.escape_burrow.x - self.x) * 0.15
            self.vy = (self.escape_burrow.y - self.y) * 0.15
            self.radius -= 0.4
            if self.radius <= 1:
                self.radius = 0.0

        if self.vx != 0.0 or self.vy != 0.0:
            self.angle = math.atan2(self.vy, self.vx)
            self.anim_cycle += 0.25

        super().update(arena_w, arena_h, obstacles, lakes, bridges)

    def draw(self, surface, camera_x, camera_y):
        if self.radius <= 0:
            return

        local_w, local_h = 50, 50
        local_surf = pygame.Surface((local_w, local_h), pygame.SRCALPHA)
        cx, cy = local_w // 2, local_h // 2

        # Hop offset simulation
        hop_offset = 0 if self.state == 'idle' else -int(abs(math.sin(self.anim_cycle)) * 4)

        # White Tail
        pygame.draw.circle(local_surf, (255, 255, 255), (cx - 7, cy + hop_offset), 3)

        # Body
        pygame.draw.ellipse(local_surf, self.color, (cx - 9, cy - 7 + hop_offset, 18, 14))

        # Head
        pygame.draw.ellipse(local_surf, self.color, (cx + 2, cy - 6.5 + hop_offset, 10, 9))

        # Ears
        ear_wiggle = math.sin(self.anim_cycle) * 0.15
        ear_surf = pygame.Surface((12, 16), pygame.SRCALPHA)
        pygame.draw.ellipse(ear_surf, self.color, (4, 0, 4, 12))
        pygame.draw.ellipse(ear_surf, (255, 192, 203), (5, 2, 2, 8))
        
        # Rotate ears
        rotated_ears = pygame.transform.rotate(ear_surf, math.degrees(-math.pi/4 + ear_wiggle))
        local_surf.blit(rotated_ears, (cx + 2, cy - 14 + hop_offset))

        # Eye
        pygame.draw.circle(local_surf, (0, 0, 0), (cx + 8, cy - 4 + hop_offset), 1)

        # Blit
        deg = -math.degrees(self.angle)
        rotated_surf = pygame.transform.rotate(local_surf, deg)
        new_rect = rotated_surf.get_rect(center=(int(self.x - camera_x), int(self.y - camera_y)))
        surface.blit(rotated_surf, new_rect.topleft)


# 3. PREDATOR (WOLF)
class Wolf(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 22, (127, 140, 141))
        self.base_speed = 1.9
        self.speed = self.base_speed
        
        self.state = 'patrol'
        self.patrol_timer = 0
        self.patrol_target_x = x
        self.patrol_target_y = y
        
        self.alert_anim_timer = 0
        self.anim_cycle = random.uniform(0, 100)

    def update(self, arena_w, arena_h, obstacles, player, is_night, particles, sound_controller, lakes, bridges):
        dist_to_player = math.hypot(self.x - player.x, self.y - player.y)
        vision_radius = 290 if is_night else 210

        can_see_player = (dist_to_player < 45) if player.is_hidden else (dist_to_player < vision_radius)

        if self.state == 'patrol':
            self.speed = self.base_speed
            if can_see_player:
                self.state = 'chase'
                self.alert_anim_timer = 45
                sound_controller.play("alert")
            else:
                self.patrol_timer -= 1
                if self.patrol_timer <= 0 or math.hypot(self.x - self.patrol_target_x, self.y - self.patrol_target_y) < 20:
                    self.patrol_timer = random.randint(180, 360)
                    self.patrol_target_x = random.uniform(0, arena_w)
                    self.patrol_target_y = random.uniform(0, arena_h)
                
                angle = math.atan2(self.patrol_target_y - self.y, self.patrol_target_x - self.x)
                self.vx = math.cos(angle) * self.speed
                self.vy = math.sin(angle) * self.speed
        elif self.state == 'chase':
            self.speed = self.base_speed * 1.9 if is_night else self.base_speed * 1.55

            if not can_see_player:
                self.state = 'cooldown'
                self.patrol_timer = 90
                self.patrol_target_x = player.x; self.patrol_target_y = player.y
            else:
                angle = math.atan2(player.y - self.y, player.x - self.x)
                self.vx = math.cos(angle) * self.speed
                self.vy = math.sin(angle) * self.speed
                
                if random.random() < 0.1:
                    particles.spawn_dust(self.x, self.y)
        elif self.state == 'cooldown':
            self.speed = self.base_speed * 0.9
            self.patrol_timer -= 1
            if can_see_player:
                self.state = 'chase'
                self.alert_anim_timer = 30
            elif self.patrol_timer <= 0:
                self.state = 'patrol'
            else:
                angle = math.atan2(self.patrol_target_y - self.y, self.patrol_target_x - self.x)
                self.vx = math.cos(angle) * self.speed
                self.vy = math.sin(angle) * self.speed

        if self.alert_anim_timer > 0:
            self.alert_anim_timer -= 1

        if self.vx != 0.0 or self.vy != 0.0:
            target_angle = math.atan2(self.vy, self.vx)
            diff = target_angle - self.angle
            while diff < -math.pi: diff += math.pi * 2
            while diff > math.pi: diff -= math.pi * 2
            self.angle += diff * 0.12
            self.anim_cycle += 0.18

        super().update(arena_w, arena_h, obstacles, lakes, bridges)

    def draw(self, surface, camera_x, camera_y):
        # Draw Exclamation point above if alerted
        if self.alert_anim_timer > 0 and self.state == 'chase':
            font = pygame.font.SysFont('Arial', 24, bold=True)
            txt = font.render('!', True, (255, 71, 87))
            surface.blit(txt, (int(self.x - camera_x - txt.get_width()//2), int(self.y - camera_y - 40)))

        local_w, local_h = 100, 100
        local_surf = pygame.Surface((local_w, local_h), pygame.SRCALPHA)
        cx, cy = local_w // 2, local_h // 2

        # 1. Tail
        tail_wiggle = math.sin(self.anim_cycle) * 0.2
        tail_angle = math.pi + tail_wiggle
        tip_x = cx - 15 + math.cos(tail_angle) * 22
        tip_y = cy + math.sin(tail_angle) * 22
        
        pts = [
            (cx - 12, cy - 4),
            (cx - 20, cy + tail_wiggle * 5),
            (tip_x, tip_y),
            (cx - 12, cy + 4)
        ]
        pygame.draw.polygon(local_surf, (95, 108, 109), pts)

        # 2. Legs
        legs_color = (44, 62, 80)
        leg_offset = int(math.sin(self.anim_cycle) * 7)
        pygame.draw.rect(local_surf, legs_color, (cx - 8, cy - 16 + leg_offset, 4, 6))
        pygame.draw.rect(local_surf, legs_color, (cx + 4, cy - 16 - leg_offset, 4, 6))
        pygame.draw.rect(local_surf, legs_color, (cx - 8, cy + 10 - leg_offset, 4, 6))
        pygame.draw.rect(local_surf, legs_color, (cx + 4, cy + 10 + leg_offset, 4, 6))

        # 3. Main Muscle Body
        pygame.draw.ellipse(local_surf, self.color, (cx - 21, cy - 14, 42, 28))
        # Shoulder cape
        pygame.draw.ellipse(local_surf, (79, 92, 93), (cx - 10, cy - 13, 28, 26))

        # 4. Head / Snout
        head_pts = [
            (cx + 12, cy - 9),
            (cx + 25, cy - 3),
            (cx + 25, cy + 3),
            (cx + 12, cy + 9)
        ]
        pygame.draw.polygon(local_surf, self.color, head_pts)
        
        # Snout nose
        pygame.draw.circle(local_surf, (17, 17, 17), (cx + 25, cy), 3)

        # Ears
        pygame.draw.polygon(local_surf, (44, 62, 80), [(cx + 12, cy - 7), (cx + 5, cy - 15), (cx + 9, cy - 4)])
        pygame.draw.polygon(local_surf, (44, 62, 80), [(cx + 12, cy + 7), (cx + 5, cy + 15), (cx + 9, cy + 4)])

        # Glowing Red Eyes
        pygame.draw.circle(local_surf, (255, 51, 51), (cx + 16, cy - 4), 2)
        pygame.draw.circle(local_surf, (255, 51, 51), (cx + 16, cy + 4), 2)

        # Rotate
        deg = -math.degrees(self.angle)
        rotated_surf = pygame.transform.rotate(local_surf, deg)
        new_rect = rotated_surf.get_rect(center=(int(self.x - camera_x), int(self.y - camera_y)))
        surface.blit(rotated_surf, new_rect.topleft)


# 4. IMPASSABLE LAKE
class Lake:
    def __init__(self, x, y, width, height, shape='rect', radius=0.0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.shape = shape # 'rect' or 'circle'
        self.radius = radius
        self.rect = pygame.Rect(x - width//2, y - height//2, width, height)

    def contains(self, px, py):
        if self.shape == 'circle':
            return math.hypot(px - self.x, py - self.y) < self.radius
        else:
            return self.rect.collidepoint(px, py)

    def draw(self, surface, camera_x, camera_y):
        draw_x = int(self.x - camera_x)
        draw_y = int(self.y - camera_y)
        
        if self.shape == 'circle':
            # Outer shore
            pygame.draw.circle(surface, (14, 45, 75), (draw_x, draw_y), int(self.radius))
            # Core water
            pygame.draw.circle(surface, (10, 35, 60), (draw_x, draw_y), int(self.radius - 6))
            # Wave detail
            if self.radius > 40:
                pygame.draw.arc(surface, (40, 75, 110), (draw_x - 30, draw_y - 20, 60, 40), 0.1, 1.5, 2)
        else:
            rect = pygame.Rect(self.rect.x - camera_x, self.rect.y - camera_y, self.width, self.height)
            pygame.draw.rect(surface, (14, 45, 75), rect, border_radius=12)
            pygame.draw.rect(surface, (10, 35, 60), rect.inflate(-12, -12), border_radius=8)
            # Wave detail
            if self.width > 60 and self.height > 60:
                pygame.draw.arc(surface, (40, 75, 110), (rect.centerx - 20, rect.centery - 15, 40, 30), 0.1, 1.5, 2)


# 5. WALKABLE BRIDGE
class Bridge:
    def __init__(self, x, y, width, height, shape='rect', radius=0.0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.shape = shape
        self.radius = radius
        self.rect = pygame.Rect(x - width//2, y - height//2, width, height)

    def contains(self, px, py):
        if self.shape == 'circle':
            return math.hypot(px - self.x, py - self.y) < self.radius
        return self.rect.collidepoint(px, py)

    def draw(self, surface, camera_x, camera_y):
        draw_x = int(self.x - camera_x)
        draw_y = int(self.y - camera_y)
        
        if self.shape == 'circle':
            # Draw circular grass island
            pygame.draw.circle(surface, (14, 45, 25), (draw_x, draw_y), int(self.radius))
            pygame.draw.circle(surface, (6, 19, 9), (draw_x, draw_y), int(self.radius - 6))
            return

        rect = pygame.Rect(self.rect.x - camera_x, self.rect.y - camera_y, self.width, self.height)
        
        # Draw wooden base
        pygame.draw.rect(surface, (120, 80, 45), rect, border_radius=2)
        pygame.draw.rect(surface, (80, 50, 25), rect, width=2, border_radius=2)
        
        # Planks
        if self.width > self.height: # Horizontal bridge
            for px in range(rect.x + 4, rect.x + self.width, 16):
                pygame.draw.line(surface, (90, 60, 30), (px, rect.y), (px, rect.y + self.height), 2)
                # nails
                pygame.draw.circle(surface, (40, 40, 40), (px + 1, rect.y + 4), 1.5)
                pygame.draw.circle(surface, (40, 40, 40), (px + 1, rect.y + self.height - 4), 1.5)
        else: # Vertical bridge
            for py in range(rect.y + 4, rect.y + self.height, 16):
                pygame.draw.line(surface, (90, 60, 30), (rect.x, py), (rect.x + self.width, py), 2)
                # nails
                pygame.draw.circle(surface, (40, 40, 40), (rect.x + 4, py + 1), 1.5)
                pygame.draw.circle(surface, (40, 40, 40), (rect.x + self.width - 4, py + 1), 1.5)


# 6. MAGICAL PORTAL (Next Map gateway)
class Portal:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 26
        self.angle = 0.0
        self.active = False

    def update(self):
        if self.active:
            self.angle += 0.08

    def draw(self, surface, camera_x, camera_y):
        if not self.active:
            return
            
        draw_x = int(self.x - camera_x)
        draw_y = int(self.y - camera_y)
        
        # Spinning vortex
        for r in [self.radius, self.radius - 7, self.radius - 14]:
            rot = self.angle * (1.5 if r % 2 == 0 else -1.0)
            
            temp_surf = pygame.Surface((r * 2 + 10, r * 2 + 10), pygame.SRCALPHA)
            cx = temp_surf.get_width() // 2
            cy = temp_surf.get_height() // 2
            
            color = (46, 204, 113, 160) if r % 2 == 0 else (241, 196, 15, 160)
            pygame.draw.circle(temp_surf, color, (cx, cy), r, width=3)
            
            # Spinning teeth
            for i in range(6):
                a = rot + (i / 6.0) * math.pi * 2.0
                tx = cx + math.cos(a) * r
                ty = cy + math.sin(a) * r
                pygame.draw.circle(temp_surf, (255, 255, 255, 220), (int(tx), int(ty)), 3)
                
            surface.blit(temp_surf, (draw_x - cx, draw_y - cy))


# 7. MUD (Slower zone)
class Mud:
    def __init__(self, x, y, radius_x, radius_y, angle):
        self.x = x
        self.y = y
        self.radius_x = radius_x
        self.radius_y = radius_y
        self.angle = angle
        self.radius = max(radius_x, radius_y)

    def contains(self, entity):
        cos_val = math.cos(-self.angle)
        sin_val = math.sin(-self.angle)
        dx = entity.x - self.x
        dy = entity.y - self.y
        rx = dx * cos_val - dy * sin_val
        ry = dx * sin_val + dy * cos_val
        return ((rx * rx) / (self.radius_x * self.radius_x) + (ry * ry) / (self.radius_y * self.radius_y)) <= 1.0

    def draw(self, surface, camera_x, camera_y):
        w = int(self.radius_x * 2 + 10)
        h = int(self.radius_y * 2 + 10)
        temp_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = w // 2, h // 2
        
        pygame.draw.ellipse(temp_surf, (35, 50, 39, 140), (cx - self.radius_x, cy - self.radius_y, self.radius_x * 2, self.radius_y * 2))
        pygame.draw.ellipse(temp_surf, (28, 41, 31, 140), (cx - self.radius_x + 6, cy - self.radius_y + 6, (self.radius_x - 6) * 2, (self.radius_y - 6) * 2))
        
        rotated_surf = pygame.transform.rotate(temp_surf, math.degrees(self.angle))
        rect = rotated_surf.get_rect(center=(int(self.x - camera_x), int(self.y - camera_y)))
        surface.blit(rotated_surf, rect.topleft)


# 8. BUSH (Stealth Zone)
class Bush:
    def __init__(self, x, y, radius):
        self.x = x
        self.y = y
        self.radius = radius
        self.leaves = []
        leaf_count = 5
        for i in range(leaf_count):
            a = (i / leaf_count) * math.pi * 2
            dist = radius * 0.45
            self.leaves.append({
                'x': math.cos(a) * dist,
                'y': math.sin(a) * dist,
                'r': radius * 0.65
            })

    def draw(self, surface, camera_x, camera_y):
        draw_x = int(self.x - camera_x)
        draw_y = int(self.y - camera_y)
        
        # Outer leaves
        for leaf in self.leaves:
            lx = int(draw_x + leaf['x'])
            ly = int(draw_y + leaf['y'])
            pygame.draw.circle(surface, (33, 140, 78), (lx, ly), int(leaf['r']))
            
        # Inner core
        pygame.draw.circle(surface, (46, 204, 113), (draw_x, draw_y), int(self.radius * 0.7))


# 9. BURROW (Rabbit escape hole)
class Burrow:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 14

    def draw(self, surface, camera_x, camera_y):
        draw_x = int(self.x - camera_x)
        draw_y = int(self.y - camera_y)
        
        # Brown rim
        pygame.draw.circle(surface, (26, 16, 5), (draw_x, draw_y), int(self.radius))
        # Black opening
        pygame.draw.circle(surface, (6, 4, 1), (draw_x, draw_y), int(self.radius - 3))


# 10. WILD BERRY
class Berry:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 8
        self.bounce_timer = random.uniform(0, 100)

    def draw(self, surface, camera_x, camera_y):
        self.bounce_timer += 0.08
        float_y = int(math.sin(self.bounce_timer) * 3)
        draw_x = int(self.x - camera_x)
        draw_y = int(self.y - camera_y) + float_y
        
        # Leaves
        pygame.draw.ellipse(surface, (39, 174, 96), (draw_x - 6, draw_y - 5, 6, 4))
        pygame.draw.ellipse(surface, (39, 174, 96), (draw_x, draw_y - 5, 6, 4))
        
        # Red berries
        pygame.draw.circle(surface, (231, 76, 60), (draw_x - 3, draw_y + 2), 4)
        pygame.draw.circle(surface, (231, 76, 60), (draw_x + 3, draw_y + 2), 4)
        pygame.draw.circle(surface, (231, 76, 60), (draw_x, draw_y - 1), 4)
        
        # Shine
        pygame.draw.circle(surface, (255, 118, 117), (draw_x - 1, draw_y - 2), 1)
