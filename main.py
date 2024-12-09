import tkinter as tk
from frequency_sweeper.gui.app import FrequencySweeperApp

def main():
    root = tk.Tk()
    app = FrequencySweeperApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
