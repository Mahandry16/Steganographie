import wave
import struct
import os
import random


class AudioSteganography:
    def __init__(self, audio_path):
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Le fichier audio {audio_path} n'existe pas")

        self.audio_path = audio_path
        self.wave_read = wave.open(audio_path, 'rb')
        self.nchannels = self.wave_read.getnchannels()
        self.sampwidth = self.wave_read.getsampwidth()
        self.framerate = self.wave_read.getframerate()
        self.nframes = self.wave_read.getnframes()
        self.comptype = self.wave_read.getcomptype()
        self.compname = self.wave_read.getcompname()

        self.frames = self.wave_read.readframes(self.nframes)
        self.wave_read.close()

        total_samples = self.nframes * self.nchannels
        if self.sampwidth == 1:
            fmt = f"{total_samples}B"
        elif self.sampwidth == 2:
            fmt = f"<{total_samples}h"
        else:
            raise ValueError("Seuls les fichiers 8-bit ou 16-bit sont supportés")

        self.samples = list(struct.unpack(fmt, self.frames))
        self.metadata_samples = 32  # Pour stocker longueur et shift
        self.byte_positions = []

    def hide_binary_file(self, txt_path, output_audio_path, positions_file=None, shift=0):
        binary_str = self._read_and_validate_binary_file(txt_path)
        padding = (8 - len(binary_str) % 8) % 8  # Calcul du padding
        byte_data = self._bits_to_bytes(binary_str)

        # Générer 1 position de départ par octet (chaque octet utilise 8 échantillons)
        self._load_or_generate_positions(positions_file, len(byte_data))

        if positions_file is not None:
            with open(positions_file, 'w') as f:
                for pos in self.byte_positions:
                    f.write(f"{pos}\n")

        if len(byte_data) > len(self.byte_positions):
            raise ValueError(
                f"Capacité insuffisante. Max: {len(self.byte_positions)} octets, Reçu: {len(byte_data)} octets")

        # Stocker le padding dans les métadonnées
        self._store_metadata(len(byte_data), shift, padding)  # <-- Modification ici

        for i, byte in enumerate(byte_data):
            sample_idx = self.byte_positions[i]
            # Stocker les 8 bits de l'octet dans 8 échantillons consécutifs
            for bit_pos in range(8):
                if sample_idx + bit_pos >= len(self.samples):
                    continue
                bit = (byte >> (7 - bit_pos)) & 1  # Extraire le bit (MSB en premier)
                self.samples[sample_idx + bit_pos] = (self.samples[sample_idx + bit_pos] & ~(1 << shift)) | (
                            bit << shift)

        self._save_audio(output_audio_path)

    def retrieve_binary_file(self, output_txt_path=None, positions_file=None):
        length, shift, padding = self._extract_metadata()  # <-- Récupérer le padding
        self._load_or_generate_positions(positions_file, length)

        extracted_bytes = bytearray()
        for i in range(length):
            sample_idx = self.byte_positions[i]
            byte = 0
            for bit_pos in range(8):
                if sample_idx + bit_pos >= len(self.samples):
                    continue
                bit = (self.samples[sample_idx + bit_pos] >> shift) & 1
                byte = (byte << 1) | bit
            extracted_bytes.append(byte)

        binary_str = ''.join(format(byte, '08b') for byte in extracted_bytes)
        binary_str = binary_str[:length * 8 - padding]  # <-- Supprimer le padding

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
            max_pos = len(self.samples) - 8  # On a besoin de 8 échantillons consécutifs par byte

            while len(self.byte_positions) < required_length:
                pos = random.randint(0, max_pos)
                if pos not in existing_positions:
                    self.byte_positions.append(pos)
                    existing_positions.add(pos)

    def _store_metadata(self, length, shift, padding):
        metadata = (length & 0xFFFF) | ((shift & 0xFF) << 16) | ((padding & 0x7) << 24)  # 3 bits pour le padding
        metadata_bits = format(metadata, '032b')

        for i in range(self.metadata_samples):
            if i < 32:
                self.samples[i] = (self.samples[i] & ~1) | int(metadata_bits[i])

    def _extract_metadata(self):
        metadata_bits = []
        for i in range(self.metadata_samples):
            if i < 32:
                metadata_bits.append(str(self.samples[i] & 1))

        metadata = int(''.join(metadata_bits), 2)
        length = metadata & 0xFFFF
        shift = (metadata >> 16) & 0xFF
        padding = (metadata >> 24) & 0x7  # Récupérer le padding
        return length, shift, padding

        return length, shift

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

    def _save_audio(self, output_audio_path):
        total_samples = len(self.samples)
        if self.sampwidth == 1:
            fmt = f"{total_samples}B"
        elif self.sampwidth == 2:
            fmt = f"<{total_samples}h"
        data = struct.pack(fmt, *self.samples)

        wave_write = wave.open(output_audio_path, 'wb')
        wave_write.setnchannels(self.nchannels)
        wave_write.setsampwidth(self.sampwidth)
        wave_write.setframerate(self.framerate)
        wave_write.setcomptype(self.comptype, self.compname)
        wave_write.writeframes(data)
        wave_write.close()

# Exemple d'utilisation:
# audio_stego = AudioSteganography("input.wav")
# audio_stego.hide_binary_file("message.txt", "output.wav", "positions.txt", shift=1)
#
# audio_stego = AudioSteganography("output.wav")
# recovered_bits = audio_stego.retrieve_binary_file("recovered.txt", "positions.txt")