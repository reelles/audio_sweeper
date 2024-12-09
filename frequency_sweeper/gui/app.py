import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from .channel import FrequencySweeperChannel

class FrequencySweeperApp:
    def __init__(self, master):
        self.master = master
        self.channels = []
        self.setup_gui()
        
        # Agregar protocolo de cierre
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_gui(self):
        """Configura la interfaz de usuario"""
        self.master.title("Frequency Sweeper")
        
        # Crear el notebook (pestañas)
        self.notebook = ttk.Notebook(self.master)
        self.notebook.grid(row=0, column=0, padx=10, pady=10)

        # Crear canales de sonido
        self.channels = {}
        self.prev_sweeps = []
        self.channel_lines = {}

        # Configurar el gráfico y los controles
        self.setup_plot()
        self.setup_controls()
        self.add_new_channel()

    def setup_plot(self):
        """Configura el gráfico de matplotlib"""
        self.figure, self.ax_waveform = plt.subplots(1, 1, figsize=(8, 4))
        self.ax_waveform.set_xlim(0, 0.01)
        self.ax_waveform.set_ylim(-1.2, 1.2)
        self.ax_waveform.set_xlabel("Time (s)")
        self.ax_waveform.set_ylabel("Amplitude")
        self.ax_waveform.grid(True)
        self.ax_waveform.set_title("Oscilloscope View")

        self.canvas = FigureCanvasTkAgg(self.figure, master=self.master)
        self.canvas.get_tk_widget().grid(column=0, row=1, padx=10, pady=10)

    def setup_controls(self):
        """Configura los controles principales de la aplicación"""
        self.add_channel_button = ttk.Button(
            self.master, 
            text="Add Channel", 
            command=self.add_new_channel
        )
        self.add_channel_button.grid(row=2, column=0, padx=10, pady=10)

    def add_new_channel(self):
        """Crea una nueva pestaña para cada canal"""
        channel_name = f"Canal {len(self.channels) + 1}"
        new_channel_frame = ttk.Frame(self.notebook)
        new_channel = FrequencySweeperChannel(new_channel_frame, channel_name, self)
        self.channels[channel_name] = new_channel
        self.notebook.add(new_channel_frame, text=channel_name)

    def add_to_prev_sweeps(self, sweep):
        """Añade un barrido a la lista de barridos previos"""
        self.prev_sweeps.append(sweep)

    def delete_channel(self, channel_name):
        """Elimina un canal de la lista"""
        if channel_name in self.channels:
            del self.channels[channel_name]
            if channel_name in self.channel_lines:
                self.channel_lines[channel_name].remove()
                del self.channel_lines[channel_name]
                self.ax_waveform.legend()
                self.canvas.draw()

    def update_waveform(self, channel_name, time, waveform):
        """Actualiza la forma de onda de un canal"""
        try:
            if channel_name not in self.channel_lines:
                line, = self.ax_waveform.plot([], [], label=channel_name)
                self.channel_lines[channel_name] = line
                self.ax_waveform.legend()

            self.channel_lines[channel_name].set_data(time, waveform)
            self.ax_waveform.relim()
            self.ax_waveform.autoscale_view()
            self.canvas.draw()
        except Exception as e:
            print(f"Error updating waveform: {e}")

    def on_closing(self):
        """Maneja el cierre de la aplicación"""
        try:
            # Detener todos los canales activos
            for channel in self.channels:
                if hasattr(channel, 'is_playing') and channel.is_playing:
                    channel.stop_sweep()
        except Exception as e:
            print(f"Error during closing: {e}")
        finally:
            # Asegurar que la ventana se cierre incluso si hay errores
            self.master.destroy()