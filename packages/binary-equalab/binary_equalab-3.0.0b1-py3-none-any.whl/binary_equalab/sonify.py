
import numpy as np
import wave
import struct
import os
from typing import Union, List
import sympy as sp
from .parser_enhanced import EnhancedParser

class AudioEngine:
    """
    Las matemáticas también suenan.
    Converts math expressions to .wav audio files.
    """
    
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        
    def generate(self, expr_str: str, duration: float = 3.0, filename: str = "output.wav"):
        """
        Evaluate expression f(t) and save as WAV.
        t is time in seconds.
        """
        # Parse expression to SymPy
        # We need a secure parsing way that allows 't' symbol
        t = sp.symbols('t')
        
        # Preprocess using our EnhancedParser (supports 2t, sin^2(t))
        clean_expr = EnhancedParser.preprocess(expr_str)
        # Also standardize python power
        clean_expr = clean_expr.replace('^', '**')
        
        try:
            # Parse with SymPy
            sym_expr = sp.sympify(clean_expr)
            # Create lambda for fast numeric evaluation
            f = sp.lambdify(t, sym_expr, modules=['numpy', 'math'])
        except Exception as e:
            raise ValueError(f"Error parsing '{expr_str}': {e}")
            
        print(f"🎵 Synthesizing: {clean_expr} for {duration}s...")
        
        # Generate Time Array
        t_arr = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # Evaluate function
        try:
            audio_data = f(t_arr)
            
            # Handle scalar result (e.g. "440")
            if np.isscalar(audio_data):
                audio_data = np.full_like(t_arr, float(audio_data))
                
        except Exception as e:
            raise ValueError(f"Math Error: {e}")
            
        # Normalize and Clip to -1..1
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            audio_data = audio_data / max_val * 0.9  # Normalize and leave headroom
        else:
            # Silence
            pass
            
        # Convert to 16-bit PCM
        # audio_data is float -1..1
        audio_int16 = (audio_data * 32767).astype(np.int16)
        
        # Save WAV
        try:
            with wave.open(filename, 'w') as wav_file:
                # 1 Channel (Mono), 2 bytes (16 bit), Sample Rate, Count, Method
                wav_file.setparams((1, 2, self.sample_rate, len(audio_int16), 'NONE', 'not compressed'))
                
                # Write frames
                # struct.pack isn't efficient for arrays, use tobytes()
                wav_file.writeframes(audio_int16.tobytes())
                
            print(f"✅ Saved audio to: {os.path.abspath(filename)}")
            return os.path.abspath(filename)
            
        except Exception as e:
            raise IOError(f"File Error: {e}")

# Standalone CLI test
if __name__ == "__main__":
    engine = AudioEngine()
    # A440 Sine Wave
    engine.generate("sin(440*2*pi*t)", duration=2.0, filename="test_tone.wav")
    # AM Synthesis (Tremolo)
    engine.generate("sin(440*2*pi*t) * (0.5 + 0.5*sin(5*2*pi*t))", duration=3.0, filename="test_tremolo.wav")
