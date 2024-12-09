import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy.signal import chirp, square, sawtooth

class FrequencySweeper:
    def __init__(self, root):
        self.root = root
        self.root.title("Frequency Sweeper")
        
        self.start_freq = tk.DoubleVar(value=5000.0)
        self.end_freq = tk.DoubleVar(value=10000.0)
        self.duration = tk.IntVar(value=10)
        self.waveform_type = tk.StringVar(value="sinusoidal")
        
        self.sample_rate = 44100
        self.create_widgets()
        self.stop_update = False
        self.prev_sweeps = []
        self.current_line = None
        self.stream = None
        self.max_point, = self.ax.plot([], [], 'ro')  # Point for max frequency
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        controls_frame = ttk.Frame(self.root)
        controls_frame.grid(column=0, row=0, padx=10, pady=10)
        
        ttk.Label(controls_frame, text="Start Frequency (Hz):").grid(column=0, row=0, padx=10, pady=5)
        self.start_freq_entry = ttk.Entry(controls_frame, textvariable=self.start_freq)
        self.start_freq_entry.grid(column=1, row=0, padx=10, pady=5)
        
        ttk.Label(controls_frame, text="End Frequency (Hz):").grid(column=0, row=1, padx=10, pady=5)
        self.end_freq_entry = ttk.Entry(controls_frame, textvariable=self.end_freq)
        self.end_freq_entry.grid(column=1, row=1, padx=10, pady=5)
        
        ttk.Label(controls_frame, text="Duration (s):").grid(column=0, row=2, padx=10, pady=5)
        self.duration_entry = ttk.Entry(controls_frame, textvariable=self.duration)
        self.duration_entry.grid(column=1, row=2, padx=10, pady=5)
        
        ttk.Label(controls_frame, text="Waveform:").grid(column=0, row=3, padx=10, pady=5)
        self.waveform_sinusoidal = ttk.Radiobutton(controls_frame, text="Sinusoidal", variable=self.waveform_type, value="sinusoidal")
        self.waveform_square = ttk.Radiobutton(controls_frame, text="Cuadrada", variable=self.waveform_type, value="square")
        self.waveform_sawtooth = ttk.Radiobutton(controls_frame, text="Sierra", variable=self.waveform_type, value="sawtooth")
        self.waveform_triangle = ttk.Radiobutton(controls_frame, text="Triangular", variable=self.waveform_type, value="triangle")
        
        self.waveform_sinusoidal.grid(column=1, row=3, padx=10, pady=5, sticky='w')
        self.waveform_square.grid(column=1, row=4, padx=10, pady=5, sticky='w')
        self.waveform_sawtooth.grid(column=1, row=5, padx=10, pady=5, sticky='w')
        self.waveform_triangle.grid(column=1, row=6, padx=10, pady=5, sticky='w')
        
        self.play_button = ttk.Button(controls_frame, text="Play", command=self.play_sweep)
        self.play_button.grid(column=0, row=7, padx=10, pady=20)
        
        self.stop_button = ttk.Button(controls_frame, text="Stop", command=self.stop_sweep)
        self.stop_button.grid(column=1, row=7, padx=10, pady=20)
        
        self.figure, (self.ax, self.ax_waveform) = plt.subplots(2, 1)
        self.ax.set_xlim(0, self.sample_rate // 2)
        self.ax.set_ylim(0, 1)
        self.ax.grid()
        self.lines = []
        self.colors = iter(plt.cm.rainbow(np.linspace(0, 1, 10)))
        
        self.waveform_line, = self.ax_waveform.plot([], [])  # Line for waveform
        self.ax_waveform.set_xlim(0, 0.001)  # Display 10 ms of audio
        self.ax_waveform.set_ylim(-1, 1)
        self.ax_waveform.grid()
        
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.root)
        self.canvas.get_tk_widget().grid(column=1, row=0, padx=10, pady=10)
    
    def play_sweep(self):
        self.stop_sweep()  # Ensure any previous sweep is stopped
        
        self.stop_update = False
        start_freq = self.start_freq.get()
        end_freq = self.end_freq.get()
        duration = self.duration.get()
        waveform_type = self.waveform_type.get()
        
        if duration < 1 or duration > 120:
            messagebox.showerror("Error", "Duration must be between 1 and 120 seconds")
            return

        # Clean up previous line data and prepare new line
        if (start_freq, end_freq) in self.prev_sweeps:
            index = self.prev_sweeps.index((start_freq, end_freq))
            line = self.lines[index]
            line.set_data([], [])  # Clear previous line data
        else:
            self.prev_sweeps.append((start_freq, end_freq))
            color = next(self.colors)
            line, = self.ax.plot([], [], lw=2, color=color)
            self.lines.append(line)
        
        self.current_line = line

        # Generate audio signal based on waveform type
        t = np.linspace(0, duration, int(self.sample_rate * duration), endpoint=False)
        if waveform_type == "sinusoidal":
            self.audio = chirp(t, f0=start_freq, f1=end_freq, t1=duration, method='linear').astype(np.float32)
        elif waveform_type == "square":
            self.audio = square(2 * np.pi * chirp(t, f0=start_freq, f1=end_freq, t1=duration, method='linear')).astype(np.float32)
        elif waveform_type == "sawtooth":
            self.audio = sawtooth(2 * np.pi * chirp(t, f0=start_freq, f1=end_freq, t1=duration, method='linear')).astype(np.float32)
        elif waveform_type == "triangle":
            self.audio = sawtooth(2 * np.pi * chirp(t, f0=start_freq, f1=end_freq, t1=duration, method='linear'), 0.5).astype(np.float32)
        
        # Initialize and start audio stream
        self.stream = sd.OutputStream(callback=self.audio_callback, samplerate=self.sample_rate, channels=1)
        self.stream.start()
        
        self.update_plot()

    def audio_callback(self, outdata, frames, time, status):
        size = len(self.audio)
        outframes = min(size, frames)
        outdata[:outframes, 0] = self.audio[:outframes]
        
        if outframes < frames:
            outdata[outframes:, 0].fill(0)
            raise sd.CallbackStop()
        
        self.audio = self.audio[outframes:]
    
    def stop_sweep(self):
        self.stop_update = True
        if self.stream is not None:
            self.stream.stop(ignore_errors=True)
            self.stream.close(ignore_errors=True)
        self.current_line = None
        self.canvas.draw()
    
    def update_plot(self):
        if not self.stop_update and len(self.audio) > 0 and self.current_line:
            current_audio = self.audio[:int(self.sample_rate * 0.1)]
            if len(current_audio) > 0:
                # Update FFT plot
                fft = np.fft.fft(current_audio)
                freqs = np.fft.fftfreq(len(fft), 1 / self.sample_rate)
                
                y = np.abs(fft[:len(fft) // 2])
                x = freqs[:len(fft) // 2]
                
                self.current_line.set_data(x, y / np.max(y))
                
                max_freq = x[np.argmax(y)]
                max_val = np.max(y / np.max(y))
                
                for annotation in self.ax.texts:
                    annotation.remove()
                
                self.max_point.set_data([max_freq], [max_val])
                self.annotation = self.ax.annotate(f'{max_freq:.2f} Hz', xy=(max_freq, max_val), xytext=(-20,20),
                                                   textcoords='offset points',
                                                   arrowprops=dict(arrowstyle="->", color='red'))
                self.annotation.set_visible(True)
                
                # Update waveform plot
                self.waveform_line.set_data(np.linspace(0, 0.01, len(current_audio[:int(self.sample_rate * 0.01)])), 
                                            current_audio[:int(self.sample_rate * 0.01)])
                
                self.canvas.draw()
            self.root.after(10, self.update_plot)
        else:
            self.stop_sweep()  # Ensure the sweep stops automatically at the end
    def on_closing(self):
        self.stop_sweep()
        self.root.quit()  # Ensures the Tkinter event loop exits
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = FrequencySweeper(root)
    root.mainloop()
