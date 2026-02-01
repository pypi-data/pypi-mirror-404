import numpy as np

def generate_chirp(f0: float | int, f1: float | int, duration: float | int, sample_rate: int = 44100) -> np.ndarray:
    """
    Core function to calculate the frequency-modulated signal.
    """
    t = np.linspace(0, duration, int(sample_rate * duration))
    # Linear frequency modulation formula
    k = (f1 - f0) / duration
    phase = 2 * np.pi * (f0 * t + 0.5 * k * t**2)
    return np.sin(phase)