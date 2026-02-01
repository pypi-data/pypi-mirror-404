class PayloadCipher:
    def decrypt(self, raw_payload: bytes, key: bytes) -> bytes:
        return self._xor_with_key(raw_payload, key)

    def encrypt(self, raw_payload: bytes, key: bytes) -> bytes:
        return self._xor_with_key(raw_payload, key)

    def _xor_with_key(self, data: bytes, key: bytes):
        decrypted = b""
        for i in range(0, len(data)):
            decrypted += bytes([data[i] ^ key[i % len(key)]])
        return decrypted
