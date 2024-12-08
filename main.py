import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class FrequencySweeper:
    def __init__(self, root):
        self.root = root
        self.root.title("Frequency Sweeper")
        
        self.start_freq = tk.DoubleVar(value=5000.0)
        self.end_freq = tk.DoubleVar(value=10000.0)
        self.duration = tk.IntVar(value=10)
        
        self.sample_rate = 44100  # Initializing sample_rate
        self.create_widgets()
        self.stop_update = False
        
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
        
        self.play_button = ttk.Button(controls_frame, text="Play", command=self.play_sweep)
        self.play_button.grid(column=0, row=3, padx=10, pady=20)
        
        self.stop_button = ttk.Button(controls_frame, text="Stop", command=self.stop_sweep)
        self.stop_button.grid(column=1, row=3, padx=10, pady=20)
        
        self.figure, self.ax = plt.subplots()
        self.ax.set_xlim(0, self.sample_rate // 2)
        self.ax.set_ylim(0, 1)
        self.ax.grid()
        self.line, = self.ax.plot([], [], lw=2)
        self.point, = self.ax.plot([], [], 'ro')  # Highlighting point
        self.annotation = self.ax.annotate('', xy=(0,0), xytext=(-20,20),
                                           textcoords='offset points',
                                           arrowprops=dict(arrowstyle="->", color='red'))
        self.annotation.set_visible(False)
        
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.root)
        self.canvas.get_tk_widget().grid(column=1, row=0, padx=10, pady=10)
    
    def play_sweep(self):
        self.stop_update = False
        start_freq = self.start_freq.get()
        end_freq = self.end_freq.get()
        duration = self.duration.get()
        
        if duration < 1 or duration > 120:
            messagebox.showerror("Error", "Duration must be between 1 and 120 seconds")
            return
        
        num_samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, num_samples, endpoint=False)
        self.sweep = start_freq + (end_freq - start_freq) * t / duration
        self.audio = np.sin(2 * np.pi * self.sweep * t).astype(np.float32)
        
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
        if hasattr(self, 'stream') and self.stream.active:
            self.stream.stop()
            self.stream.close()
            self.line.set_data([], [])
            self.point.set_data([], [])
            self.annotation.set_visible(False)
            self.canvas.draw()
    
    def update_plot(self):
        if not self.stop_update and len(self.sweep) > 0:
            current_audio = self.audio[:int(self.sample_rate * 0.1)]
            if len(current_audio) > 0:
                fft = np.fft.fft(current_audio)
                freqs = np.fft.fftfreq(len(fft), 1 / self.sample_rate)
                
                y = np.abs(fft[:len(fft) // 2])
                x = freqs[:len(fft) // 2]
                
                self.line.set_data(x, y / np.max(y))
                max_freq = x[np.argmax(y)]
                max_val = np.max(y / np.max(y))
                self.point.set_data([max_freq], [max_val])
                self.annotation.xy = (max_freq, max_val)
                self.annotation.set_text(f'{max_freq:.2f} Hz')
                self.annotation.set_visible(True)
                self.canvas.draw()
            self.root.after(10, self.update_plot)

    def on_closing(self):
        self.stop_sweep()
        self.root.quit()  # Ensures the Tkinter event loop exits
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = FrequencySweeper(root)
    root.mainloop()
