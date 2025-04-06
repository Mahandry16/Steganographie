import wave
import struct
import os
import random


class AudioSteganography:
    def __init__(self, audio_path):
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Le fichier audio {audio_path} n'existe pas")
        self.audio_path = audio_path
        # Ouverture du fichier wav en lecture binaire
        self.wave_read = wave.open(audio_path, 'rb')
        self.nchannels = self.wave_read.getnchannels()
        self.sampwidth = self.wave_read.getsampwidth()
        self.framerate = self.wave_read.getframerate()
        self.nframes = self.wave_read.getnframes()
        self.comptype = self.wave_read.getcomptype()
        self.compname = self.wave_read.getcompname()

        # Lecture des frames audio
        self.frames = self.wave_read.readframes(self.nframes)
        self.wave_read.close()

        # Conversion des frames en liste d'échantillons
        total_samples = self.nframes * self.nchannels
        if self.sampwidth == 1:
            # 8-bit : échantillons non signés
            fmt = f"{total_samples}B"
        elif self.sampwidth == 2:
            # 16-bit : échantillons signés (little endian)
            fmt = f"<{total_samples}h"
        else:
            raise ValueError("Seuls les fichiers 8-bit ou 16-bit sont supportés")

        self.samples = list(struct.unpack(fmt, self.frames))
        # Nombre d'échantillons utilisés pour stocker la graine (32 bits stockés sur 32 échantillons)
        self.seed_storage_samples = 32

    def hide_binary_file(self, txt_path, output_audio_path, seed=None):
        """
        Cache le contenu d'un fichier texte contenant des bits ('0' et '1')
        dans les LSB des échantillons audio.
        """
        binary_str = self._read_and_validate_binary_file(txt_path)
        # Calcul du nombre de bits disponibles (en excluant la zone de la graine et les 32 bits pour la taille du payload)
        available_bits = len(self.samples) - self.seed_storage_samples - 32
        if len(binary_str) > available_bits:
            raise ValueError(f"Capacité insuffisante. Max: {available_bits} bits, Reçu: {len(binary_str)} bits")

        # Si la graine n'est pas fournie, on en génère une aléatoirement
        seed = seed if seed is not None else random.getrandbits(32)
        self._store_seed(seed)

        # Préparation du payload : 32 bits indiquant la longueur suivi des bits du message
        payload_bits = format(len(binary_str), '032b') + binary_str

        # Génération des positions aléatoires (sur les échantillons après la zone de la graine)
        random.seed(seed)
        positions = self._generate_positions()

        # Insertion des bits du payload dans les LSB des échantillons choisis
        for i, bit in enumerate(payload_bits):
            if i >= len(positions):
                break
            pos = positions[i]
            self.samples[pos] = (self.samples[pos] & ~1) | int(bit)

        self._save_audio(output_audio_path)

    def retrieve_binary_file(self, output_txt_path=None):
        """
        Extrait le message caché dans un fichier audio et,
        éventuellement, l'enregistre dans un fichier texte.
        """
        seed = self._extract_seed()
        random.seed(seed)
        positions = self._generate_positions()

        extracted_bits = []
        for pos in positions:
            bit = self.samples[pos] & 1
            extracted_bits.append(str(bit))
        all_bits = ''.join(extracted_bits)

        # Lecture des 32 premiers bits pour obtenir la longueur du message
        length = int(all_bits[:32], 2)
        binary_str = all_bits[32:32 + length]

        if output_txt_path:
            self._save_binary_text(binary_str, output_txt_path)

        return binary_str

    def _read_and_validate_binary_file(self, txt_path):
        if not os.path.exists(txt_path):
            raise FileNotFoundError(f"Le fichier {txt_path} n'existe pas")
        with open(txt_path, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]

        binary_str = []
        for line in lines:
            if not all(c in '01' for c in line):
                raise ValueError(f"Ligne invalide: {line}. Seuls 0 et 1 sont autorisés")
            binary_str.append(line)
        return ''.join(binary_str)

    def _save_binary_text(self, binary_str, output_path):
        with open(output_path, 'w') as f:
            for i in range(0, len(binary_str), 4):
                f.write(binary_str[i:i + 4] + '\n')

    def _store_seed(self, seed):
        """
        Stocke la graine sur les 32 premiers échantillons audio
        en modifiant le bit de poids faible de chacun.
        """
        seed_bits = format(seed, '032b')
        for i in range(self.seed_storage_samples):
            if i < 32:
                self.samples[i] = (self.samples[i] & ~1) | int(seed_bits[i])

    def _extract_seed(self):
        seed_bits = []
        for i in range(self.seed_storage_samples):
            if i < 32:
                seed_bits.append(str(self.samples[i] & 1))
        return int(''.join(seed_bits), 2)

    def _generate_positions(self):
        """
        Génère une liste de positions (indices) disponibles pour le payload,
        excluant la zone utilisée pour la graine.
        """
        positions = list(range(self.seed_storage_samples, len(self.samples)))
        random.shuffle(positions)
        return positions

    def _save_audio(self, output_audio_path):
        """
        Recrée un fichier wav à partir de la liste modifiée des échantillons.
        """
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


if __name__ == "__main__":
    # Exemple de cache
    stego_audio = AudioSteganography("../test/input.wav")
    stego_audio.hide_binary_file("../test/bits.txt", "../test/output.wav")

    # Exemple de récupération
    stego_audio = AudioSteganography("../test/output.wav")
    recovered_bits = stego_audio.retrieve_binary_file("../test/recovered.txt")
    print("Bits récupérés:", recovered_bits)
