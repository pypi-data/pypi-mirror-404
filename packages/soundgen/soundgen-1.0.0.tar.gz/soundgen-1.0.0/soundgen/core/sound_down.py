from ..utils.generate_chirp import generate_chirp
from ..utils.write_wav_file import write_wav_file

def sound_down(filename: str, start_freq: float | int, end_freq: float | int, duration: float | int) -> None:
    """
    Generates a sound with decreasing frequency and saves it to a WAV file.
    """
    # Logic check: start must be higher than end for a 'down' effect
    if start_freq <= end_freq:
        raise ValueError("For sound_down, start_freq must be greater than end_freq.")
    
    # Generate the signal using our utility
    signal = generate_chirp(start_freq, end_freq, duration)
    
    # Save the result
    write_wav_file(filename, signal)