import os
import tempfile
from hypothesis import given, settings
from hypothesis.strategies import binary
from raytoolsbox.crypto_manager import CryptoManager

# ======================================================
# Fuzz decrypt
# ======================================================
@given(binary(min_size=0, max_size=512))
@settings(max_examples=200)
def test_fuzz_decrypt_never_crash(data):
    with tempfile.TemporaryDirectory() as tmp:
        cm = CryptoManager(tmp)
        cm.generate_keys()

        result = cm.decrypt(data)

        assert result is None or isinstance(result, (str, bytes))

# ======================================================
# Fuzz verify
# ======================================================
@given(binary(min_size=0, max_size=512))
@settings(max_examples=200)
def test_fuzz_verify_never_crash(data):
    with tempfile.TemporaryDirectory() as tmp:
        cm = CryptoManager(tmp)
        cm.generate_keys()

        result = cm.verify(data)

        assert result is None or isinstance(result, (str, bytes))