from treatement.HuffmanTreat import Huffman
from treatement.ImageTreat import ImageSteganography

if __name__ == "__main__":
    # Exemple de cache
    stego = ImageSteganography("../test/hide.png")
    stego.hide_binary_file("../test/bits.txt", "../test/hideImage.png")

    # Exemple de récupération
    stego = ImageSteganography("../test/hideImage.png")
    recovered_bits = stego.retrieve_binary_file("../test/recupered.txt")

    huffman = Huffman("../test/text.txt")
    binary_dict = huffman.get_binary_dict()

    decoded_text = Huffman.decode_with_dict(recovered_bits, binary_dict)
    print(f"Message décodé: {decoded_text}")