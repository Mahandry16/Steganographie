import heapq
from collections import defaultdict


class HuffmanNode:
    def __init__(self, freq, char=None):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq


class Huffman:
    def __init__(self, file_path=None):
        self.file_path = file_path
        self.frequencies = defaultdict(int)  # Changé ici pour utiliser defaultdict
        self.codes = {}
        self.reverse_codes = {}
        self.heap = []

        if file_path:
            self._build_frequencies()
            self._build_heap()
            self._build_tree()
            self._generate_codes()
            self._build_reverse_codes()

    def _build_frequencies(self):
        with open(self.file_path, 'r', encoding='utf-8') as file:
            text = file.read()
            for char in text:
                self.frequencies[char] += 1  # Ne générera plus d'erreur KeyError

    def _build_heap(self):
        for char, freq in self.frequencies.items():
            node = HuffmanNode(freq, char)
            heapq.heappush(self.heap, node)

    def _build_tree(self):
        while len(self.heap) > 1:
            left = heapq.heappop(self.heap)
            right = heapq.heappop(self.heap)
            merged = HuffmanNode(left.freq + right.freq)
            merged.left = left
            merged.right = right
            heapq.heappush(self.heap, merged)

    def _generate_codes(self):
        if not self.heap:
            return

        root = heapq.heappop(self.heap)

        if root.char is not None:
            self.codes[root.char] = '0'
        else:
            def traverse(node, current_code):
                if node is None:
                    return
                if node.char is not None:
                    self.codes[node.char] = current_code
                    return
                traverse(node.left, current_code + '0')
                traverse(node.right, current_code + '1')

            traverse(root, '')

    def get_binary_dict(self):
        return self.codes

    def _build_reverse_codes(self):
        self.reverse_codes = {v: k for k, v in self.codes.items()}

    def decode_bits(self, bit_string):
        if not hasattr(self, 'reverse_codes'):
            raise ValueError("Le dictionnaire Huffman n'a pas été initialisé")

        current_code = ""
        decoded_text = []

        for bit in bit_string:
            current_code += bit
            if current_code in self.reverse_codes:
                decoded_text.append(self.reverse_codes[current_code])
                current_code = ""

        if current_code:
            raise ValueError("Bits résiduels non décodables trouvés")

        return ''.join(decoded_text)

    def decode_bytes(self, byte_data):
        bit_string = ''.join(format(byte, '08b') for byte in byte_data)
        return self.decode_bits(bit_string)

    @staticmethod
    def decode_with_dict(bit_string, huffman_dict):
        reverse_dict = {v: k for k, v in huffman_dict.items()}
        current_code = ""
        decoded_text = []

        for bit in bit_string:
            current_code += bit
            if current_code in reverse_dict:
                decoded_text.append(reverse_dict[current_code])
                current_code = ""

        if current_code:
            raise ValueError("Bits résiduels non décodables trouvés")

        return ''.join(decoded_text)


if __name__ == "__main__":
    huffman = Huffman("../test/text.txt")
    binary_dict = huffman.get_binary_dict()

    print("Dictionnaire binaire :")
    for char, code in sorted(binary_dict.items()):
        print(f"{repr(char)}: {code}")