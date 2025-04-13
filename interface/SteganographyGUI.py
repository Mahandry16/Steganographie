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
        self.positions_file = tk.StringVar()
        self.huffman_dict = None

        self.create_image_section()
        self.create_audio_section()
        self.create_huffman_section()
        self.create_result_section()

    def create_image_section(self):
        frame = ttk.Labelframe(self.root, text="Image", padding=10)
        frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        # Fichier Image
        ttk.Label(frame, text="Image File:").grid(row=0, column=0, sticky=W, pady=2)
        ttk.Entry(frame, textvariable=self.image_path, width=30).grid(row=0, column=1, pady=2, padx=5)

        # Boutons Browse et Positions
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=0, column=2, padx=5, pady=2)
        ttk.Button(btn_frame, text="Browse", command=self.browse_image, bootstyle="primary-outline").pack(side=LEFT,
                                                                                                          padx=2)
        ttk.Button(btn_frame, text="Positions", command=self.load_positions_file, bootstyle="warning-outline").pack(
            side=LEFT, padx=2)

        # Boutons fonctionnels
        action_frame = ttk.Frame(frame)
        action_frame.grid(row=1, column=0, columnspan=3, pady=5)
        ttk.Button(action_frame, text="Hide Message", command=self.hide_image_message, bootstyle="success").pack(
            side=LEFT, padx=5)
        ttk.Button(action_frame, text="Get Message", command=self.get_image_message, bootstyle="info").pack(side=LEFT,
                                                                                                            padx=5)

    def create_audio_section(self):
        frame = ttk.Labelframe(self.root, text="Audio", padding=10)
        frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        # Fichier Audio
        ttk.Label(frame, text="Audio File:").grid(row=0, column=0, sticky=W, pady=2)
        ttk.Entry(frame, textvariable=self.audio_path, width=30).grid(row=0, column=1, pady=2, padx=5)

        # Boutons Browse et Positions
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=0, column=2, padx=5, pady=2)
        ttk.Button(btn_frame, text="Browse", command=self.browse_audio, bootstyle="primary-outline").pack(side=LEFT,
                                                                                                          padx=2)
        ttk.Button(btn_frame, text="Positions", command=self.load_positions_file, bootstyle="warning-outline").pack(
            side=LEFT, padx=2)

        # Boutons fonctionnels
        action_frame = ttk.Frame(frame)
        action_frame.grid(row=1, column=0, columnspan=3, pady=5)
        ttk.Button(action_frame, text="Hide Message", command=self.hide_audio_message, bootstyle="success").pack(
            side=LEFT, padx=5)
        ttk.Button(action_frame, text="Get Message", command=self.get_audio_message, bootstyle="info").pack(side=LEFT,
                                                                                                            padx=5)

    def create_huffman_section(self):
        frame = ttk.Labelframe(self.root, text="Huffman", padding=10)
        frame.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nsew")

        ttk.Label(frame, text="Huffman Dictionary:").grid(row=0, column=0, sticky=W)
        self.huffman_text = tk.Text(frame, height=10, width=30)
        self.huffman_text.grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(frame, text="Load Dictionary", command=self.load_huffman, bootstyle="secondary").grid(row=2,
                                                                                                         column=0,
                                                                                                         pady=5)

    def create_result_section(self):
        frame = ttk.Labelframe(self.root, text="Results", padding=10)
        frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self.result_text = tk.Text(frame, height=5, width=60)
        self.result_text.pack(padx=5, pady=5)

    def load_positions_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if path:
            self.positions_file.set(path)
            messagebox.showinfo("Positions Loaded", f"Positions file loaded:\n{path}")

    def browse_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg")])
        if path:
            self.image_path.set(path)

    def browse_audio(self):
        path = filedialog.askopenfilename(filetypes=[("Audio files", "*.wav")])
        if path:
            self.audio_path.set(path)

    def hide_image_message(self):
        try:
            if not self.image_path.get():
                raise ValueError("Please select an image file first")

            message_path = filedialog.askopenfilename(title="Select message file")
            if not message_path:
                return

            output_path = filedialog.asksaveasfilename(
                title="Save output image",
                defaultextension=".png",
                filetypes=[("PNG files", "*.png")]
            )

            stego = ImageSteganography(self.image_path.get())
            stego.hide_binary_file(
                message_path,
                output_path,
                positions_file=self.positions_file.get()
            )
            messagebox.showinfo("Success", "Message hidden successfully!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def get_image_message(self):
        try:
            if not self.image_path.get():
                raise ValueError("Please select an image file first")
            if not self.huffman_dict:
                raise ValueError("Please load Huffman dictionary first")

            stego = ImageSteganography(self.image_path.get())
            recovered_bits = stego.retrieve_binary_file(
                output_txt_path=None,
                positions_file=self.positions_file.get()
            )

            decoded_text = Huffman.decode_with_dict(recovered_bits, self.huffman_dict)
            self.show_result("Image Decoded Message:", decoded_text)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def hide_audio_message(self):
        try:
            if not self.audio_path.get():
                raise ValueError("Please select an audio file first")

            message_path = filedialog.askopenfilename(title="Select message file")
            if not message_path:
                return

            output_path = filedialog.asksaveasfilename(
                title="Save output audio",
                defaultextension=".wav",
                filetypes=[("WAV files", "*.wav")]
            )

            stego = AudioSteganography(self.audio_path.get())
            stego.hide_binary_file(
                message_path,
                output_path,
                positions_file=self.positions_file.get()
            )
            messagebox.showinfo("Success", "Message hidden successfully!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def get_audio_message(self):
        try:
            if not self.audio_path.get():
                raise ValueError("Please select an audio file first")
            if not self.huffman_dict:
                raise ValueError("Please load Huffman dictionary first")

            stego = AudioSteganography(self.audio_path.get())
            recovered_bits = stego.retrieve_binary_file(
                output_txt_path=None,
                positions_file=self.positions_file.get()
            )

            decoded_text = Huffman.decode_with_dict(recovered_bits, self.huffman_dict)
            self.show_result("Audio Decoded Message:", decoded_text)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def show_result(self, prefix, message):
        self.result_text.delete(1.0, tk.END)
        self.result_text.tag_config("header", foreground="blue", font=("Helvetica", 10, "bold"))
        self.result_text.tag_config("content", foreground="green")
        self.result_text.insert(tk.END, prefix + "\n", "header")
        self.result_text.insert(tk.END, message, "content")

    def load_huffman(self):
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if path:
            try:
                huffman = Huffman(path)
                self.huffman_dict = huffman.get_binary_dict()
                self.huffman_text.delete(1.0, tk.END)
                for char, code in self.huffman_dict.items():
                    self.huffman_text.insert(tk.END, f"'{repr(str(char))[1:-1]}': {code}\n")
                messagebox.showinfo("Success", "Huffman dictionary loaded!")
            except Exception as e:
                messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    style = ttk.Style(theme='flatly')
    root = style.master
    app = SteganoGUI(root)
    root.mainloop()