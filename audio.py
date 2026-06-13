# Audio module containing SoundController for WildChain: Apex Hunt
import pygame
import os
import sound_gen

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
