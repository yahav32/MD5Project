class Conversions:
    def n_to_decimal(word, alphabet):
            base = len(alphabet)
            index_map = {ch: i for i, ch in enumerate(alphabet)}  # lookup table

            value = 0
            for ch in word:
                digit = index_map[ch]
                value = value * base + digit
            return value
    def decimal_to_n(n, alphabet, length):
        base = len(alphabet)
        chars = []
        for _ in range(length):
            n, rem = divmod(n, base)
            chars.append(alphabet[rem])
        return ''.join(reversed(chars))