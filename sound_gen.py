# Programmatic WAV sound generator for WildChain: Apex Hunt (Pygame Port)
import math
import struct
import wave
import os
import random

SAMPLE_RATE = 22050

def write_wav(filename, samples):
    # Ensure directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with wave.open(filename, 'wb') as wav_file:
        # Mono, 16-bit PCM (2 bytes), SAMPLE_RATE
        wav_file.setparams((1, 2, SAMPLE_RATE, len(samples), 'NONE', 'not compressed'))
        for sample in samples:
            # Clamp sample to 16-bit range
            val = int(max(-32767, min(32767, sample * 32767)))
            wav_file.writeframes(struct.pack('<h', val))

def generate_catch():
    # Ascending frequency sweep (bell)
    samples = []
    duration = 0.22
    num_samples = int(SAMPLE_RATE * duration)
    phase = 0.0
    
    for i in range(num_samples):
        t = i / num_samples
        # Exponential frequency sweep: 280Hz -> 880Hz
        freq = 280.0 + (880.0 - 280.0) * (t ** 1.8)
        phase += 2.0 * math.pi * freq / SAMPLE_RATE
        
        # Triangle wave
        val = math.asin(math.sin(phase)) * (2.0 / math.pi)
        # Exponential decay envelope
        env = math.exp(-t * 6.0) * 0.3
        
        samples.append(val * env)
    return samples

def generate_dash():
    # Whoosh sound using modulated noise
    samples = []
    duration = 0.25
    num_samples = int(SAMPLE_RATE * duration)
    
    # Generate white noise and run a moving average filter to simulate sweeping lowpass
    raw_noise = [random.uniform(-1.0, 1.0) for _ in range(num_samples)]
    
    for i in range(num_samples):
        t = i / num_samples
        # Window size drops from 28 down to 2, opening the filter frequency
        window = int(28 * (1.0 - t)) + 2
        
        # Apply moving average filter
        start = max(0, i - window)
        filtered_val = sum(raw_noise[start:i+1]) / (i - start + 1)
        
        # Envelope rises and falls
        env = math.sin(t * math.pi) * 0.45
        samples.append(filtered_val * env)
    return samples

def generate_hurt():
    # Low pitch crash / rumble
    samples = []
    duration = 0.32
    num_samples = int(SAMPLE_RATE * duration)
    phase = 0.0
    
    for i in range(num_samples):
        t = i / num_samples
        # Falling frequency: 120Hz -> 35Hz
        freq = 120.0 - (120.0 - 35.0) * t
        phase += 2.0 * math.pi * freq / SAMPLE_RATE
        
        # Sawtooth wave mixed with noise for gravelly crunch
        synth_val = (2.0 * (phase / (2.0 * math.pi) - math.floor(phase / (2.0 * math.pi) + 0.5)))
        noise_val = random.uniform(-1.0, 1.0)
        mixed_val = (synth_val * 0.7) + (noise_val * 0.3)
        
        # Envelope decays
        env = (1.0 - t) * 0.5
        samples.append(mixed_val * env)
    return samples

def generate_alert():
    # Exclamation bip-bip
    samples = []
    duration = 0.22
    num_samples = int(SAMPLE_RATE * duration)
    phase = 0.0
    
    for i in range(num_samples):
        t = i / num_samples
        if t < 0.08:
            # First beep: 1200Hz
            freq = 1200.0
            env = 0.18
        elif t < 0.12:
            # Silence
            freq = 0.0
            env = 0.0
        else:
            # Second beep: 1000Hz
            freq = 1000.0
            env = 0.18 * math.exp(-(t - 0.12) * 10.0)
            
        if freq > 0:
            phase += 2.0 * math.pi * freq / SAMPLE_RATE
            val = math.sin(phase)
        else:
            val = 0.0
            
        samples.append(val * env)
    return samples

def generate_night():
    # Howling rise-fall
    samples = []
    duration = 1.6
    num_samples = int(SAMPLE_RATE * duration)
    phase = 0.0
    
    for i in range(num_samples):
        t = i / num_samples
        # Rise and fall frequency: 220Hz -> 480Hz -> 300Hz
        if t < 0.4:
            freq = 220.0 + (480.0 - 220.0) * (t / 0.4)
        elif t < 0.8:
            freq = 480.0 + (520.0 - 480.0) * ((t - 0.4) / 0.4)
        else:
            freq = 520.0 - (520.0 - 300.0) * ((t - 0.8) / 0.8)
            
        phase += 2.0 * math.pi * freq / SAMPLE_RATE
        val = math.sin(phase)
        
        # Envelope swells up then decays
        if t < 0.4:
            env = (t / 0.4) * 0.18
        else:
            env = math.exp(-(t - 0.4) * 2.2) * 0.18
            
        samples.append(val * env)
    return samples

def generate_heartbeat():
    # Single heartbeat waveform (double-thump)
    samples = []
    duration = 0.28
    num_samples = int(SAMPLE_RATE * duration)
    
    phase1 = 0.0
    phase2 = 0.0
    delay_samples = int(SAMPLE_RATE * 0.12)
    
    for i in range(num_samples):
        val = 0.0
        
        # First thump
        if i < int(SAMPLE_RATE * 0.15):
            t1 = i / int(SAMPLE_RATE * 0.15)
            freq1 = 55.0 - (55.0 - 20.0) * t1
            phase1 += 2.0 * math.pi * freq1 / SAMPLE_RATE
            val += math.sin(phase1) * math.exp(-t1 * 5.0) * 0.5
            
        # Second thump (delayed)
        if i >= delay_samples:
            i2 = i - delay_samples
            t2 = i2 / int(SAMPLE_RATE * 0.12)
            if t2 < 1.0:
                freq2 = 48.0 - (48.0 - 15.0) * t2
                phase2 += 2.0 * math.pi * freq2 / SAMPLE_RATE
                val += math.sin(phase2) * math.exp(-t2 * 6.0) * 0.4
                
        samples.append(val)
    return samples

def generate_all_sounds(target_dir="sounds"):
    os.makedirs(target_dir, exist_ok=True)
    
    generators = {
        "catch.wav": generate_catch,
        "dash.wav": generate_dash,
        "hurt.wav": generate_hurt,
        "alert.wav": generate_alert,
        "night.wav": generate_night,
        "heartbeat.wav": generate_heartbeat,
    }
    
    for name, gen in generators.items():
        path = os.path.join(target_dir, name)
        if not os.path.exists(path):
            print(f"Synthesizing {name}...")
            write_wav(path, gen())
            
if __name__ == "__main__":
    generate_all_sounds()
