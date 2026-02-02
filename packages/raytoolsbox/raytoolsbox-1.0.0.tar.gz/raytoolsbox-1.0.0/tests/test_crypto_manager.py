import os
import pytest
from pathlib import Path
from raytoolsbox.crypto_manager import CryptoManager

# ======================================================
# fixtures
# ======================================================
@pytest.fixture
def workdir(tmp_path):
    key_dir = tmp_path / "keys"
    data_dir = tmp_path / "data"
    key_dir.mkdir()
    data_dir.mkdir()
    return key_dir, data_dir

@pytest.fixture
def crypto(workdir):
    key_dir, _ = workdir
    cm = CryptoManager(key_dir)
    cm.generate_keys()
    return cm

# ======================================================
# 基础正确性（必须 100% 通过）
# ======================================================
def test_text_roundtrip(crypto):
    text = "Hello ✅ 世界"
    packet = crypto.encrypt(text)
    assert crypto.decrypt(packet) == text

def test_bytes_roundtrip(crypto):
    data = os.urandom(64)
    packet = crypto.encrypt(data)
    assert crypto.decrypt(packet) == data

def test_empty_text(crypto):
    packet = crypto.encrypt("")
    assert crypto.decrypt(packet) == ""

def test_large_payload(crypto):
    data = os.urandom(1024 * 1024)  # 1 MB
    packet = crypto.encrypt(data)
    assert crypto.decrypt(packet) == data

# ======================================================
# 文件 I/O 行为
# ======================================================
def test_file_encrypt_decrypt(workdir, crypto):
    _, data_dir = workdir
    src = data_dir / "秘密.txt"
    src.write_text("文件内容测试", encoding="utf-8")

    crypto.encrypt(data_path=src, save="on")
    enc_file = src.with_suffix(".txt.enc")
    assert enc_file.exists()

    result = crypto.decrypt(enc_data_path=enc_file, save="on")
    assert result == src.read_bytes()

    out = data_dir / "秘密_decrypt.txt"
    assert out.exists()
    assert out.read_bytes() == src.read_bytes()
    
# ======================================================
# 安全性：错误一定要失败
# ======================================================
def test_ciphertext_bitflip_fails(crypto):
    packet = crypto.encrypt("tamper-test")
    broken = bytearray(packet)
    broken[-1] ^= 0x01
    assert crypto.decrypt(bytes(broken)) is None

def test_magic_corruption_fails(crypto):
    packet = crypto.encrypt("magic-test")
    broken = bytearray(packet)
    broken[:4] = b"FAKE"
    assert crypto.decrypt(bytes(broken)) is None

def test_version_corruption_fails(crypto):
    packet = crypto.encrypt("version-test")
    broken = bytearray(packet)
    broken[4] = 0xFF
    assert crypto.decrypt(bytes(broken)) is None

def test_random_bytes_never_crash(crypto):
    for _ in range(50):
        garbage = os.urandom(128)
        assert crypto.decrypt(garbage) is None

# ======================================================
# 密钥隔离
# ======================================================
def test_wrong_private_key_cannot_decrypt(workdir):
    key_dir1, _ = workdir
    key_dir2 = key_dir1.parent / "other_keys"
    key_dir2.mkdir()

    cm1 = CryptoManager(key_dir1)
    cm1.generate_keys()

    cm2 = CryptoManager(key_dir2)
    cm2.generate_keys()

    packet = cm1.encrypt("top-secret")
    assert cm2.decrypt(packet) is None

# ======================================================
# 签名 / 验签
# ======================================================
def test_sign_verify_text(crypto):
    text = "signed-message"
    signed = crypto.sign(text)
    assert crypto.verify(signed) == text

def test_signature_tamper_detected(crypto):
    signed = bytearray(crypto.sign("hello"))
    signed[-1] ^= 0xFF
    assert crypto.verify(bytes(signed)) is None

def test_signature_wrong_key_fails(workdir):
    key_dir, _ = workdir

    cm1 = CryptoManager(key_dir / "a")
    cm1.generate_keys()

    cm2 = CryptoManager(key_dir / "b")
    cm2.generate_keys()

    signed = cm1.sign("msg")
    assert cm2.verify(signed) is None