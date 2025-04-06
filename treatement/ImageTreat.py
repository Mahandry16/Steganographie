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

    def hide_binary_file(self, txt_path, output_img_path, seed=None):
        binary_str = self._read_and_validate_binary_file(txt_path)

        byte_data = self._bits_to_bytes(binary_str)

        available_bits = (len(self.pixels) * 3 - self.seed_storage_pixels * 3 - 32)
        if len(binary_str) > available_bits:
            raise ValueError(f"Capacité insuffisante. Max: {available_bits} bits, Reçu: {len(binary_str)} bits")

        seed = seed if seed is not None else random.getrandbits(32)

        self._store_seed(seed)

        payload_bits = format(len(binary_str), '032b') + binary_str

        random.seed(seed)
        positions = self._generate_positions()

        new_pixels = list(self.pixels)
        for i, bit in enumerate(payload_bits):
            if i >= len(positions):
                break

            idx, channel = positions[i]
            r, g, b = new_pixels[idx]

            if channel == 0:
                r = (r & 0xFE) | int(bit)
            elif channel == 1:
                g = (g & 0xFE) | int(bit)
            else:
                b = (b & 0xFE) | int(bit)

            new_pixels[idx] = (r, g, b)

        self._save_image(new_pixels, output_img_path)

    def retrieve_binary_file(self, output_txt_path=None):
        seed = self._extract_seed()
        random.seed(seed)

        positions = self._generate_positions()

        extracted_bits = []
        for idx, channel in positions:
            r, g, b = self.pixels[idx]

            if channel == 0:
                extracted_bits.append(str(r & 1))
            elif channel == 1:
                extracted_bits.append(str(g & 1))
            else:
                extracted_bits.append(str(b & 1))

        all_bits = ''.join(extracted_bits)

        length = int(all_bits[:32], 2)
        binary_str = all_bits[32:32 + length]

        if output_txt_path:
            self._save_binary_text(binary_str, output_txt_path)

        return binary_str

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
        # Ajout de padding si la longueur n'est pas un multiple de 8
        padding = (8 - len(binary_str) % 8) % 8
        padded_str = binary_str + '0' * padding

        # Conversion en bytes
        return bytes(int(padded_str[i:i + 8], 2) for i in range(0, len(padded_str), 8))

    def _bytes_to_bits(self, byte_data, bit_length):

        full_bits = ''.join(format(byte, '08b') for byte in byte_data)
        return full_bits[:bit_length]

    def _save_binary_text(self, binary_str, output_path):
        with open(output_path, 'w') as f:
            for i in range(0, len(binary_str), 4):
                f.write(binary_str[i:i + 4] + '\n')

    def _store_seed(self, seed):
        seed_bits = format(seed, '032b')
        new_pixels = list(self.pixels)
        bit_idx = 0

        for i in range(self.seed_storage_pixels):
            if bit_idx >= 32:
                break

            r, g, b = new_pixels[i]

            if bit_idx < 32:
                r = (r & 0xFE) | int(seed_bits[bit_idx])
                bit_idx += 1
            if bit_idx < 32:
                g = (g & 0xFE) | int(seed_bits[bit_idx])
                bit_idx += 1
            if bit_idx < 32:
                b = (b & 0xFE) | int(seed_bits[bit_idx])
                bit_idx += 1

            new_pixels[i] = (r, g, b)

        self.pixels = new_pixels

    def _extract_seed(self):
        seed_bits = []

        for i in range(self.seed_storage_pixels):
            r, g, b = self.pixels[i]
            seed_bits.extend([str(r & 1), str(g & 1), str(b & 1)])

        return int(''.join(seed_bits[:32]), 2)

    def _generate_positions(self):
        positions = []
        for idx in range(self.seed_storage_pixels, len(self.pixels)):
            positions.extend([(idx, 0), (idx, 1), (idx, 2)])

        random.shuffle(positions)
        return positions

    def _save_image(self, pixels, output_path):
        new_image = Image.new('RGB', (self.width, self.height))
        new_image.putdata(pixels)
        new_image.save(output_path)


# if __name__ == "__main__":
#     # Exemple de cache
#     stego = ImageSteganography("../test/hide.png")
#     stego.hide_binary_file("../test/bits.txt", "../test/hideImage.png")
#
#     # Exemple de récupération
#     stego = ImageSteganography("../test/hideImage.png")
#     recovered_bits = stego.retrieve_binary_file("../test/recupered.txt")
#     print("Bits récupérés:", recovered_bits)