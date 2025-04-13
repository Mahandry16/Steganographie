from treatement.AudioTreat import AudioSteganography
from treatement.HuffmanTreat import Huffman
from treatement.ImageTreat import ImageSteganography

if __name__ == "__main__":
    stego = ImageSteganography("../test/hide.png")
    stego.hide_binary_file("../test/hideImage1.txt", "../test/hideImage.png")

    stego_audio = AudioSteganography("../test/input.wav")
    stego_audio.hide_binary_file("../test/hideMessage2.txt", "../test/output.wav")

    stego = ImageSteganography("../test/hideImage.png")
    recovered_bits = stego.retrieve_binary_file("../test/recupered.txt")

    stego_audio = AudioSteganography("../test/output.wav")
    recover_bits = stego_audio.retrieve_binary_file("../test/recovered.txt")

    huffman = Huffman("../test/text.txt")
    binary_dict = huffman.get_binary_dict()

    decoded_text = Huffman.decode_with_dict(recovered_bits, binary_dict)
    print(f"Message image décodé: {decoded_text}")

    decodeded_text = Huffman.decode_with_dict(recover_bits, binary_dict)
    print(f"Message audio décodé: {decodeded_text}")

