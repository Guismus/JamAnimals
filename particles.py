# Particles module for WildChain: Apex Hunt (Pygame Port)
import pygame
import random
import math

def draw_circle_alpha(surface, color, center, radius):
    """Draw a circle with alpha transparency onto a surface."""
    if color[3] >= 255:
        pygame.draw.circle(surface, color[:3], (int(center[0]), int(center[1])), int(radius))
        return
        
    x = int(center[0] - radius)
    y = int(center[1] - radius)
    r_int = int(radius)
    
    # Create surface with alpha channel
    temp_surf = pygame.Surface((r_int * 2, r_int * 2), pygame.SRCALPHA)
    pygame.draw.circle(temp_surf, color, (r_int, r_int), r_int)
    surface.blit(temp_surf, (x, y))

def draw_rect_alpha(surface, color, rect, angle=0):
    """Draw a rotated rectangle with alpha transparency onto a surface."""
    w, h = rect.width, rect.height
    temp_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    temp_surf.fill(color)
    
    if angle != 0:
        rotated_surf = pygame.transform.rotate(temp_surf, math.degrees(angle))
        new_rect = rotated_surf.get_rect(center=rect.center)
        surface.blit(rotated_surf, new_rect.topleft)
    else:
        surface.blit(temp_surf, rect.topleft)

class Particle:
    def __init__(self, x, y, vx, vy, color, size, life, decay, shape='circle', gravity=0.0, rot_speed=0.0, glow=False):
        self.x = x; self.y = y
        self.vx = vx; self.vy = vy
        self.color = color # (R, G, B, A)
        self.size = size
        self.alpha = color[3]
        self.life = life
        self.max_life = life
        self.decay = decay
        self.shape = shape
        self.gravity = gravity
        self.rotation = random.uniform(0, math.pi * 2)
        self.rot_speed = rot_speed
        self.glow = glow

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.rotation += self.rot_speed
        
        # Decay alpha
        self.alpha -= self.decay * 255
        self.life -= 1
        return self.life > 0 and self.alpha > 0

    def draw(self, surface, camera_x, camera_y):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        
        # Fade color alpha
        current_alpha = max(0, min(255, int(self.alpha)))
        color_with_alpha = (self.color[0], self.color[1], self.color[2], current_alpha)
        
        if self.shape == 'square':
            rect = pygame.Rect(0, 0, int(self.size), int(self.size))
            rect.center = (int(draw_x), int(draw_y))
            draw_rect_alpha(surface, color_with_alpha, rect, self.rotation)
        else:
            draw_circle_alpha(surface, color_with_alpha, (draw_x, draw_y), self.size)


class ParticleSystem:
    def __init__(self):
        self.particles = []
        self.quality = 'high' # 'high' or 'low'

    def update(self):
        self.particles = [p for p in self.particles if p.update()]

    def draw(self, surface, camera_x, camera_y):
        for p in self.particles:
            # Simple viewport culling
            w, h = surface.get_size()
            if -50 <= p.x - camera_x <= w + 50 and -50 <= p.y - camera_y <= h + 50:
                p.draw(surface, camera_x, camera_y)

    def clear(self):
        self.particles.clear()

    def spawn_dust(self, x, y):
        if self.quality == 'low' and random.random() < 0.7:
            return
        count = 1 if random.random() < 0.4 else 2
        for _ in range(count):
            vx = random.uniform(-0.4, 0.4)
            vy = random.uniform(-0.5, -0.2)
            color = (125, 138, 110, 200) if random.random() < 0.5 else (168, 176, 155, 200)
            size = random.uniform(2.0, 5.0)
            life = random.randint(25, 40)
            self.particles.append(Particle(
                x, y, vx, vy, color, size, life, 1.0 / life
            ))

    def spawn_splash(self, x, y):
        if self.quality == 'low' and random.random() < 0.7:
            return
        count = random.randint(3, 5)
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(0.5, 2.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - 1.0
            color = (74, 122, 140, 220) # Muddy blue
            size = random.uniform(2.0, 4.0)
            life = random.randint(20, 30)
            self.particles.append(Particle(
                x, y, vx, vy, color, size, life, 1.0 / life, gravity=0.08
            ))

    def spawn_leaves(self, x, y):
        if self.quality == 'low' and random.random() < 0.7:
            return
        count = random.randint(4, 7)
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(0.4, 1.6)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            color = (46, 204, 113, 230) if random.random() < 0.6 else (39, 174, 96, 230)
            size = random.uniform(4.0, 8.0)
            life = random.randint(30, 50)
            self.particles.append(Particle(
                x, y, vx, vy, color, size, life, 1.0 / life,
                shape='square', rot_speed=random.uniform(-0.1, 0.1)
            ))

    def spawn_bite(self, x, y):
        if self.quality == 'low' and random.random() < 0.7:
            return
        count = random.randint(12, 19)
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1.5, 5.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            color = (231, 76, 60, 255) if random.random() < 0.7 else (192, 57, 43, 255) # Red
            size = random.uniform(1.5, 5.0)
            life = random.randint(25, 40)
            self.particles.append(Particle(
                x, y, vx, vy, color, size, life, 1.0 / life, gravity=0.05
            ))

    def spawn_eat(self, x, y, is_berry=False):
        if self.quality == 'low' and random.random() < 0.7:
            return
        count = random.randint(8, 11)
        color = (241, 196, 15, 255) if is_berry else (231, 76, 60, 255)
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(0.5, 2.5)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            size = random.uniform(1.5, 4.5)
            life = random.randint(20, 30)
            self.particles.append(Particle(
                x, y, vx, vy, color, size, life, 1.0 / life, glow=is_berry
            ))

    def spawn_fireflies(self, view_w, view_h, camera_x, camera_y):
        if self.quality == 'low' and random.random() < 0.7:
            return
        x = camera_x + random.uniform(0, view_w)
        y = camera_y + random.uniform(0, view_h)
        vx = random.uniform(-0.2, 0.2)
        vy = random.uniform(-0.2, 0.2)
        color = (209, 242, 165, 180) # Soft yellow-green
        size = random.uniform(1.0, 3.0)
        life = random.randint(150, 250)
        self.particles.append(Particle(
            x, y, vx, vy, color, size, life, 1.0 / life, glow=True
        ))
