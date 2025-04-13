from PIL import Image
import random
import math
import os


class ImageSteganography:
    def __init__(self, image_path):
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Le fichier image {image_path} n'existe pas")

        self.image_path = image_path
        self.image = Image.open(image_path)

        if self.image.mode != 'RGB':
            self.image = self.image.convert('RGB')

        self.pixels = list(self.image.getdata())
        self.width = self.image.width
        self.height = self.image.height
        self.seed_storage_pixels = 11
        self.byte_positions = []

    def hide_binary_file(self, txt_path, output_img_path, positions_file=None, shift=0):
        binary_str = self._read_and_validate_binary_file(txt_path)
        padding = (8 - len(binary_str) % 8) % 8
        byte_data = self._bits_to_bytes(binary_str)

        # Charger 8 positions par octet
        self._load_or_generate_positions(positions_file, 8 * len(byte_data))  # <-- Modification ici

        if positions_file is not None:
            with open(positions_file, 'w') as f:
                for pos in self.byte_positions:
                    f.write(f"{pos}\n")

        if 8 * len(byte_data) > len(self.byte_positions):  # <-- Modification ici
            raise ValueError(
                f"Capacité insuffisante. Max: {len(self.byte_positions) // 8} bytes, Reçu: {len(byte_data)} bytes")

        self._store_metadata(len(byte_data), shift, padding)

        new_pixels = list(self.pixels)
        for i, byte in enumerate(byte_data):
            for bit_pos in range(8):  # Stocker chaque bit dans une position distincte
                idx = i * 8 + bit_pos
                if idx >= len(self.byte_positions):
                    break

                pos = self.byte_positions[idx]
                pixel_idx = pos // 3
                channel = pos % 3

                if pixel_idx >= len(new_pixels):
                    continue

                # Extraire le bit (du MSB au LSB)
                bit = (byte >> (7 - bit_pos)) & 1  # <-- Modification ici

                # Modifier le LSB du canal
                r, g, b = new_pixels[pixel_idx]
                if channel == 0:
                    new_val = ((r >> shift) & 0xFE) | bit
                    new_pixels[pixel_idx] = (new_val << shift if shift > 0 else new_val, g, b)
                elif channel == 1:
                    new_val = ((g >> shift) & 0xFE) | bit
                    new_pixels[pixel_idx] = (r, new_val << shift if shift > 0 else new_val, b)
                else:
                    new_val = ((b >> shift) & 0xFE) | bit
                    new_pixels[pixel_idx] = (r, g, new_val << shift if shift > 0 else new_val)

        self._save_image(new_pixels, output_img_path)

    def retrieve_binary_file(self, output_txt_path=None, positions_file=None):
        length, shift, padding = self._extract_metadata()

        # Charger 8 positions par octet
        self._load_or_generate_positions(positions_file, 8 * length)  # <-- Modification ici

        extracted_bytes = bytearray()
        for i in range(length):
            byte = 0
            for bit_pos in range(8):  # Lire 8 bits pour former l'octet
                idx = i * 8 + bit_pos
                if idx >= len(self.byte_positions):
                    break

                pos = self.byte_positions[idx]
                pixel_idx = pos // 3
                channel = pos % 3

                if pixel_idx >= len(self.pixels):
                    continue

                r, g, b = self.pixels[pixel_idx]
                if channel == 0:
                    val = (r >> shift) & 1
                elif channel == 1:
                    val = (g >> shift) & 1
                else:
                    val = (b >> shift) & 1

                byte = (byte << 1) | val  # <-- Modification ici

            extracted_bytes.append(byte)

        binary_str = ''.join(format(byte, '08b') for byte in extracted_bytes)
        binary_str = binary_str[:length * 8 - padding]

        if output_txt_path:
            self._save_binary_text(binary_str, output_txt_path)

        return binary_str

    def _load_or_generate_positions(self, positions_file, required_length):
        self.byte_positions = []

        if positions_file and os.path.exists(positions_file):
            with open(positions_file, 'r') as f:
                self.byte_positions = [int(line.strip()) for line in f if line.strip()]

        # Si pas assez de positions, compléter avec des positions aléatoires
        if len(self.byte_positions) < required_length:
            random.seed(42)  # Seed fixe pour la reproductibilité
            existing_positions = set(self.byte_positions)
            max_pos = len(self.pixels) * 3 - 1
            additional_positions = []

            while len(additional_positions) < (required_length - len(self.byte_positions)):
                pos = random.randint(0, max_pos)
                if pos not in existing_positions:
                    additional_positions.append(pos)
                    existing_positions.add(pos)

            self.byte_positions.extend(additional_positions)

    def _store_metadata(self, length, shift, padding):
        metadata = (length & 0xFFFF) | ((shift & 0xFF) << 16) | ((padding & 0x7) << 24)
        metadata_bits = format(metadata, '032b')

        new_pixels = list(self.pixels)
        bit_idx = 0

        for i in range(self.seed_storage_pixels):
            if bit_idx >= 32:
                break

            r, g, b = new_pixels[i]

            if bit_idx < 32:
                r = (r & 0xFE) | int(metadata_bits[bit_idx])
                bit_idx += 1
            if bit_idx < 32:
                g = (g & 0xFE) | int(metadata_bits[bit_idx])
                bit_idx += 1
            if bit_idx < 32:
                b = (b & 0xFE) | int(metadata_bits[bit_idx])
                bit_idx += 1

            new_pixels[i] = (r, g, b)

        self.pixels = new_pixels

    def _extract_metadata(self):
        metadata_bits = []

        for i in range(self.seed_storage_pixels):
            r, g, b = self.pixels[i]
            metadata_bits.extend([str(r & 1), str(g & 1), str(b & 1)])

        metadata = int(''.join(metadata_bits[:32]), 2)
        length = metadata & 0xFFFF
        shift = (metadata >> 16) & 0xFF
        padding = (metadata >> 24) & 0x7  # Récupérer le padding
        return length, shift, padding

    def _read_and_validate_binary_file(self, txt_path):
        if not os.path.exists(txt_path):
            raise FileNotFoundError(f"Le fichier {txt_path} n'existe pas")

        with open(txt_path, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        binary_str = []
        for line in lines:
            if not all(c in {'0', '1'} for c in line):
                raise ValueError(f"Ligne invalide: {line}. Seuls 0 et 1 sont autorisés")
            binary_str.append(line)

        return ''.join(binary_str)

    def _bits_to_bytes(self, binary_str):
        padding = (8 - len(binary_str) % 8) % 8
        padded_str = binary_str + '0' * padding
        return bytes(int(padded_str[i:i + 8], 2) for i in range(0, len(padded_str), 8))

    def _save_binary_text(self, binary_str, output_path):
        with open(output_path, 'w') as f:
            for i in range(0, len(binary_str), 4):
                f.write(binary_str[i:i + 4] + '\n')

    def _save_image(self, pixels, output_path):
        new_image = Image.new('RGB', (self.width, self.height))
        new_image.putdata(pixels)
        new_image.save(output_path)

# Exemple d'utilisation:
# stego = ImageSteganography("image.png")
# stego.hide_binary_file("message.txt", "output.png", "positions.txt", shift=1)
#
# stego = ImageSteganography("output.png")
# recovered_bits = stego.retrieve_binary_file("recovered.txt", "positions.txt")