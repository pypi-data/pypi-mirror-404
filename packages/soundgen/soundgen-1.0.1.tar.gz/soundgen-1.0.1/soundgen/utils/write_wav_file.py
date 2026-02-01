import wave
import struct
import numpy as np

def write_wav_file(filename: str, signal: np.ndarray, sample_rate: int = 44100) -> None:
    """
    Converts a signal array to a physical 16-bit PCM .wav file.
    """
    # Auto-add extension if missing
    if not filename.endswith('.wav'):
        filename += '.wav'
        
    # Scale signal to 16-bit integer range [-32768, 32767]
    # We assume the input signal is normalized between -1.0 and 1.0
    amplitude = 32767
    data = (signal * amplitude).astype(np.int16)
    
    # Open file for writing
    with wave.open(filename, 'w') as f:
        # Configuration: Mono channel, 2 bytes per sample, specified sample rate
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        
        # Write frames: '<h' means little-endian short integer (16-bit)
        for value in data:
            f.writeframes(struct.pack('<h', value))