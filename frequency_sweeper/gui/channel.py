import tkinter as tk
from tkinter import ttk, messagebox
import sounddevice as sd
import numpy as np

from frequency_sweeper.utils.config import (
    SAMPLE_RATE, 
    BUFFER_SIZE, 
    MIN_DURATION, 
    MAX_DURATION, 
    DEFAULT_VOLUME,
    WAVEFORM_TYPES,
    SWEEP_TYPES,
    generate_sweep
)

__all__ = ['FrequencySweeperChannel']

class FrequencySweeperChannel:
    def __init__(self, parent, channel_name, main_app):
        self.parent = parent
        self.channel_name = channel_name
        self.main_app = main_app
        self.sample_rate = SAMPLE_RATE
        self.setup_variables()
        self.create_widgets()

    def setup_variables(self):
        """Inicializa todas las variables del canal"""
        # Variables de audio
        self.audio = None
        self.original_audio = None
        self.stream = None
        self.stop_update = False
        self.is_playing = False
        self.current_position = 0
        
        # Variables de control
        self.start_freq = tk.DoubleVar(value=5000.0)
        self.end_freq = tk.DoubleVar(value=10000.0)
        self.duration = tk.IntVar(value=10)
        self.waveform_type = tk.StringVar(value="sinusoidal")
        self.channel_label = tk.StringVar(value=self.channel_name)
        self.sweep_type = tk.StringVar(value="forward")
        self.volume = tk.DoubleVar(value=DEFAULT_VOLUME)
        self.is_muted = tk.BooleanVar(value=False)
        self.previous_volume = DEFAULT_VOLUME
        self.loop = tk.BooleanVar(value=False)

    def create_widgets(self):
        """Crea todos los widgets del canal"""
        # Frame principal de controles
        controls_frame = ttk.Frame(self.parent)
        controls_frame.grid(column=0, row=0, padx=10, pady=10)

        self.create_basic_controls(controls_frame)
        self.create_waveform_controls(controls_frame)
        self.create_sweep_controls(controls_frame)
        self.create_volume_controls()

    def create_basic_controls(self, parent):
        """Crea los controles básicos"""
        controls = [
            ("Channel Name:", self.channel_label),
            ("Start Frequency (Hz):", self.start_freq),
            ("End Frequency (Hz):", self.end_freq),
            ("Duration (s):", self.duration)
        ]

        for i, (label, var) in enumerate(controls):
            ttk.Label(parent, text=label).grid(column=0, row=i, padx=10, pady=5)
            ttk.Entry(parent, textvariable=var).grid(column=1, row=i, padx=10, pady=5)

    def create_waveform_controls(self, parent):
        """Crea los controles de tipo de onda"""
        ttk.Label(parent, text="Waveform:").grid(column=0, row=4, padx=10, pady=5)
        
        for i, waveform in enumerate(WAVEFORM_TYPES):
            ttk.Radiobutton(
                parent, 
                text=waveform.capitalize(), 
                variable=self.waveform_type, 
                value=waveform
            ).grid(column=1, row=4+i, padx=10, pady=5, sticky='w')

    def create_sweep_controls(self, parent):
        """Crea los controles de barrido"""
        current_row = 8
        
        ttk.Label(parent, text="Sweep Type:").grid(
            column=0, row=current_row, padx=10, pady=5
        )
        
        sweep_types = ["linear", "logarithmic", "exponential"]
        self.sweep_combobox = ttk.Combobox(
            parent, 
            textvariable=self.sweep_type,
            values=sweep_types,
            state="readonly"
        )
        self.sweep_combobox.set(sweep_types[0])
        self.sweep_combobox.grid(column=1, row=current_row, padx=10, pady=5)

        # Loop checkbox
        self.loop_checkbox = ttk.Checkbutton(
            parent, 
            text="Loop", 
            variable=self.loop
        )
        self.loop_checkbox.grid(column=0, row=current_row+1, padx=10, pady=5)

        # Control buttons
        self.create_control_buttons(parent, current_row+2)

    def create_control_buttons(self, parent, row):
        """Crea los botones de control"""
        self.play_button = ttk.Button(
            parent, text="Play", command=self.play_sweep
        )
        self.play_button.grid(column=0, row=row, padx=10, pady=20)

        self.stop_button = ttk.Button(
            parent, text="Stop", command=self.stop_sweep
        )
        self.stop_button.grid(column=1, row=row, padx=10, pady=20)

        self.delete_button = ttk.Button(
            parent, text="Delete", command=self.delete_channel
        )
        self.delete_button.grid(column=0, row=row+1, padx=10, pady=5)

    def create_volume_controls(self):
        """Crea los controles de volumen"""
        volume_frame = ttk.Frame(self.parent)
        volume_frame.grid(column=1, row=0, padx=10, pady=10, sticky='ns')

        ttk.Label(volume_frame, text="Volume").grid(
            column=0, row=0, padx=5, pady=5
        )

        self.volume_slider = ttk.Scale(
            volume_frame,
            from_=100,
            to=0,
            orient='vertical',
            length=200,
            variable=self.volume,
            command=self.on_volume_change
        )
        self.volume_slider.grid(column=0, row=1, padx=5, pady=5)

        self.volume_label = ttk.Label(volume_frame, text="100%")
        self.volume_label.grid(column=0, row=2, padx=5, pady=5)

        self.mute_button = ttk.Button(
            volume_frame,
            text="Mute",
            command=self.toggle_mute,
            width=8
        )
        self.mute_button.grid(column=0, row=3, padx=5, pady=5)

    def play_sweep(self):
        """Plays the frequency sweep"""
        try:
            # Si ya está reproduciendo, pausar
            if self.is_playing:
                self.stop_sweep()
                return

            # Generate the sweep based on current parameters
            self.audio = generate_sweep(
                start_freq=self.start_freq.get(),
                end_freq=self.end_freq.get(),
                duration=self.duration.get(),
                waveform_type=self.waveform_type.get()
            )
            
            # Store original audio for potential reuse
            self.original_audio = self.audio.copy()
            
            # Apply volume
            self.audio *= self.volume.get() / 100.0
            
            # Reset stop flag
            self.stop_update = False
            
            # Create and start the audio stream
            self.stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=1,
                callback=self._audio_callback,
                finished_callback=self._on_stream_finished
            )
            
            # Update waveform display
            t = np.linspace(0, self.duration.get(), len(self.audio))
            self.main_app.update_waveform(self.channel_name, t, self.audio)
            
            self.stream.start()
            self.is_playing = True
            self.play_button.configure(text="Pause")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to play sweep: {str(e)}")

    def _audio_callback(self, outdata, frames, time, status):
        """Callback for audio stream"""
        if status:
            print(f'Audio callback status: {status}')
        
        if self.stop_update:
            outdata.fill(0)
            return
            
        if self.current_position >= len(self.audio):
            if self.loop.get():
                self.current_position = 0
            else:
                outdata.fill(0)
                raise sd.CallbackStop()
                
        chunk = self.audio[self.current_position:self.current_position + frames]
        if len(chunk) < frames:
            outdata[:len(chunk), 0] = chunk
            outdata[len(chunk):, 0] = 0
        else:
            outdata[:, 0] = chunk
        self.current_position += frames

    def _on_stream_finished(self):
        """Callback when stream is finished"""
        self.is_playing = False
        self.current_position = 0
        self.play_button.configure(text="Play")

    def stop_sweep(self):
        """Stops the frequency sweep"""
        try:
            self.stop_update = True
            if self.stream is not None:
                self.stream.stop()
                self.stream.close()
                self.stream = None
            self.is_playing = False
            self.current_position = 0
            self.play_button.configure(text="Play")
            
            # Clear waveform display
            self.main_app.update_waveform(self.channel_name, [], [])
            
        except Exception as e:
            print(f"Error stopping sweep: {e}")

    def delete_channel(self):
        """Removes this channel from the main application"""
        if self.stream is not None:
            self.stop_sweep()
        self.parent.destroy()
        if hasattr(self.main_app, 'channels'):
            self.main_app.channels.remove(self)

    def toggle_mute(self):
        """Toggles mute state"""
        if self.is_muted.get():
            # Unmute - restore previous volume
            self.volume.set(self.previous_volume)
            self.mute_button.configure(text="Mute")
        else:
            # Mute - store current volume and set to 0
            self.previous_volume = self.volume.get()
            self.volume.set(0)
            self.mute_button.configure(text="Unmute")
        self.is_muted.set(not self.is_muted.get())

    def on_volume_change(self, *args):
        """Handle volume slider changes"""
        current_volume = self.volume.get()
        self.volume_label.configure(text=f"{int(current_volume)}%")
        
        # Update audio volume if playing
        if self.audio is not None:
            self.audio = self.original_audio.copy() * (current_volume / 100.0)