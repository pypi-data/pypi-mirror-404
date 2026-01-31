import ctypes
import os


class ChutesLLMVerifier:
    def __init__(
        self,
        lib_path: str = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "lib", "libcllmv.so"
        ),
    ):
        if not os.path.exists(lib_path):
            raise FileNotFoundError(f"Shared library not found: {lib_path}")
        self.lib = ctypes.CDLL(lib_path)
        self.lib.generate.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p]
        self.lib.generate.restype = ctypes.c_char_p
        self.lib.validate.argtypes = [
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
        ]
        self.lib.validate.restype = ctypes.c_int

    def generate(self, id: str, created: int, value: str) -> str:
        result = self.lib.generate(
            id.encode("utf-8"),
            created,
            value.encode("utf-8") if value else None,
        )
        return result.decode("utf-8")

    def validate(
        self,
        id: str,
        created: int,
        value: str,
        expected_hash: str,
        salt: str,
        model: str,
        revision: str,
    ) -> bool:
        salt_ptr = salt.encode("utf-8")
        result = self.lib.validate(
            id.encode("utf-8"),
            created,
            value.encode("utf-8") if value else None,
            expected_hash.encode("utf-8"),
            salt_ptr,
            model.encode("utf-8"),
            revision.encode("utf-8"),
        )
        return bool(result)


if __name__ == "__main__":
    verifier = ChutesLLMVerifier()
    hash_value = verifier.generate(id="test-id", created=1234567890, value="test-value")
    print(f"Generated hash: {hash_value}")

    is_valid = verifier.validate(
        id="test-id",
        created=1234567890,
        value="test-value",
        expected_hash=hash_value,
        salt="6c146619-1621-4775-8c8d-cb7f256b22f4",
    )
    print(f"Hash is valid: {is_valid}")

    is_valid = verifier.validate(
        id="test-id", created=1234567890, value="test-value", expected_hash="0" * 32, salt="garble"
    )
    print(f"Wrong hash is valid: {is_valid}")
