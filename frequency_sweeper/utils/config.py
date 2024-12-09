import numpy as np
from scipy.signal import chirp, square, sawtooth

# Configuraciones globales
SAMPLE_RATE = 44100
BUFFER_SIZE = 1024
MIN_DURATION = 1
MAX_DURATION = 120
DEFAULT_VOLUME = 100.0

# Tipos de ondas disponibles
WAVEFORM_TYPES = [
    "sinusoidal",
    "square",
    "sawtooth",
    "triangle"
]

# Tipos de barrido
SWEEP_TYPES = [
    "linear",
    "logarithmic",
    "exponential"
]

def generate_sweep(start_freq, end_freq, duration, waveform_type, sample_rate=SAMPLE_RATE):
    """Genera una señal de barrido de frecuencia"""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    
    # Usamos 'linear' como método por defecto
    method = 'linear'
    
    if waveform_type == "sinusoidal":
        audio = chirp(t, f0=start_freq, f1=end_freq, t1=duration, method=method)
    elif waveform_type == "square":
        freq_t = chirp(t, f0=start_freq, f1=end_freq, t1=duration, method=method)
        audio = square(2 * np.pi * freq_t)
    elif waveform_type == "sawtooth":
        freq_t = chirp(t, f0=start_freq, f1=end_freq, t1=duration, method=method)
        audio = sawtooth(2 * np.pi * freq_t)
    elif waveform_type == "triangle":
        freq_t = chirp(t, f0=start_freq, f1=end_freq, t1=duration, method=method)
        audio = sawtooth(2 * np.pi * freq_t, width=0.5)
    
    return audio / np.max(np.abs(audio)) 