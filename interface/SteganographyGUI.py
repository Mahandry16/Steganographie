import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
from treatement.ImageTreat import ImageSteganography
from treatement.AudioTreat import AudioSteganography
from treatement.HuffmanTreat import Huffman
import os

class SteganoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Steganographie GUI")

        self.image_path = tk.StringVar()
        self.audio_path = tk.StringVar()

        self.huffman_dict = None

        self.create_image_section()
        self.create_audio_section()
        self.create_huffman_section()
        self.create_result_section()

    def create_image_section(self):
        frame = ttk.Labelframe(self.root, text="Image", padding=10)
        frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        # Lead File
        ttk.Label(frame, text="Lead File:").grid(row=0, column=0, sticky=W, pady=2)
        ttk.Entry(frame, textvariable=self.image_path, width=30).grid(row=0, column=1, pady=2, padx=5)
        ttk.Button(frame, text="Browse", command=self.browse_image, bootstyle="primary-outline").grid(row=0, column=2, padx=5, pady=2)

        # Size
        ttk.Label(frame, text="Size:").grid(row=1, column=0, sticky=W, pady=2)
        self.image_size = ttk.Label(frame, text="0 bytes")
        self.image_size.grid(row=1, column=1, sticky=W, pady=2)

        # Boutons côte à côte pour cacher et récupérer le message
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=5)
        ttk.Button(button_frame, text="Hide Message", command=self.hide_image_message, bootstyle="success").pack(side=LEFT, padx=5)
        ttk.Button(button_frame, text="Get Message", command=self.get_image_message, bootstyle="info").pack(side=LEFT, padx=5)

    def create_audio_section(self):
        frame = ttk.Labelframe(self.root, text="Audio", padding=10)
        frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        # Lead File
        ttk.Label(frame, text="Lead File:").grid(row=0, column=0, sticky=W, pady=2)
        ttk.Entry(frame, textvariable=self.audio_path, width=30).grid(row=0, column=1, pady=2, padx=5)
        ttk.Button(frame, text="Browse", command=self.browse_audio, bootstyle="primary-outline").grid(row=0, column=2, padx=5, pady=2)

        # Size
        ttk.Label(frame, text="Size:").grid(row=1, column=0, sticky=W, pady=2)
        self.audio_size = ttk.Label(frame, text="0 bytes")
        self.audio_size.grid(row=1, column=1, sticky=W, pady=2)

        # Boutons côte à côte pour cacher et récupérer le message
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=5)
        ttk.Button(button_frame, text="Hide Message", command=self.hide_audio_message, bootstyle="success").pack(side=LEFT, padx=5)
        ttk.Button(button_frame, text="Get Message", command=self.get_audio_message, bootstyle="info").pack(side=LEFT, padx=5)

    def create_huffman_section(self):
        frame = ttk.Labelframe(self.root, text="Huffman", padding=10)
        frame.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nsew")

        ttk.Label(frame, text="Content:").grid(row=0, column=0, sticky=W)
        self.huffman_text = tk.Text(frame, height=10, width=30)
        self.huffman_text.grid(row=1, column=0, padx=5, pady=5)

        ttk.Button(frame, text="Load File", command=self.load_huffman, bootstyle="secondary").grid(row=2, column=0, pady=5)

    def create_result_section(self):
        frame = ttk.Labelframe(self.root, text="Results", padding=10)
        frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        self.result_text = tk.Text(frame, height=5, width=60)
        self.result_text.pack(padx=5, pady=5)

    def browse_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg")])
        if path:
            self.image_path.set(path)
            self.image_size.config(text=f"{os.path.getsize(path)} bytes")

    def browse_audio(self):
        path = filedialog.askopenfilename(filetypes=[("Audio files", "*.wav")])
        if path:
            self.audio_path.set(path)
            self.audio_size.config(text=f"{os.path.getsize(path)} bytes")

    def hide_image_message(self):
        try:
            message_path = filedialog.askopenfilename(title="Select message file")
            if not message_path:
                return

            output_path = filedialog.asksaveasfilename(
                title="Save output image",
                defaultextension=".png",
                filetypes=[("PNG files", "*.png")]
            )
            if not output_path:
                return

            stego = ImageSteganography(self.image_path.get())
            stego.hide_binary_file(message_path, output_path)
            messagebox.showinfo("Success", "Message hidden in image successfully!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def get_image_message(self):
        try:
            if not self.huffman_dict:
                messagebox.showerror("Error", "Please load Huffman dictionary first")
                return

            stego = ImageSteganography(self.image_path.get())
            recovered_bits = stego.retrieve_binary_file()

            decoded_text = Huffman.decode_with_dict(recovered_bits, self.huffman_dict)

            self.result_text.delete(1.0, tk.END)

            self.result_text.tag_config("highlight", foreground="red", font=("Helvetica", 10, "bold"))

            self.result_text.insert(tk.END, "Image Decoded Message: ", "default")
            self.result_text.insert(tk.END, decoded_text, "highlight")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def hide_audio_message(self):
        try:
            message_path = filedialog.askopenfilename(title="Select message file")
            if not message_path:
                return

            output_path = filedialog.asksaveasfilename(
                title="Save output audio",
                defaultextension=".wav",
                filetypes=[("WAV files", "*.wav")]
            )
            if not output_path:
                return

            stego = AudioSteganography(self.audio_path.get())
            stego.hide_binary_file(message_path, output_path)
            messagebox.showinfo("Success", "Message hidden in audio successfully!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def get_audio_message(self):
        try:
            if not self.huffman_dict:
                messagebox.showerror("Error", "Please load Huffman dictionary first")
                return

            stego = AudioSteganography(self.audio_path.get())
            recovered_bits = stego.retrieve_binary_file()

            decoded_text = Huffman.decode_with_dict(recovered_bits, self.huffman_dict)

            self.result_text.delete(1.0, tk.END)

            self.result_text.tag_config("highlight", foreground="red", font=("Helvetica", 10, "bold"))

            self.result_text.insert(tk.END, "Audio Decoded Message: ", "default")
            self.result_text.insert(tk.END, decoded_text, "highlight")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def load_huffman(self):
        path = filedialog.askopenfilename()
        if path:
            try:
                huffman = Huffman(path)
                self.huffman_dict = huffman.get_binary_dict()
                self.huffman_text.delete(1.0, tk.END)
                for char, code in self.huffman_dict.items():
                    self.huffman_text.insert(tk.END, f"'{char}': {code}\n")
                messagebox.showinfo("Success", "Huffman dictionary loaded successfully!")
            except Exception as e:
                messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    style = ttk.Style(theme='flatly')
    root = style.master
    app = SteganoGUI(root)
    root.mainloop()
