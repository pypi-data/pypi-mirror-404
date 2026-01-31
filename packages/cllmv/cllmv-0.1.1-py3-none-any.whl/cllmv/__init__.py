from cllmv.base import ChutesLLMVerifier

_verifier = None


def init():
    global _verifier
    _verifier = ChutesLLMVerifier()


def generate(id: str, created: int, value: str) -> str:
    if _verifier is None:
        init()
    return _verifier.generate(id, created, value)


def validate(
    id: str, created: int, value: str, expected_hash: str, salt: str, model: str, revision: str
) -> bool:
    if _verifier is None:
        init()
    return _verifier.validate(id, created, value, expected_hash, salt, model, revision)


__all__ = [
    "ChutesLLMVerifier",
    "validate",
    "generate",
]
