import os

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import x25519, ed25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey


from pathlib import Path

class CryptoManager:
    """
    ✅ 现代化 ECC 加密管理器（无签名版）

    - 使用 X25519 进行密钥交换
    - 使用 ChaCha20-Poly1305 进行对称加密
    - 原始数据支持 str / bytes / 文件，加密或签名后返回二进制数据包
    """
    _SIGN_LEN = 64  # Ed25519 固定长度
    # 数据类型信息
    _TYPE_TEXT = b"\x01"
    _TYPE_BYTES = b"\x02"
    # 二进制格式数据包指纹
    _MAGIC = b"ECC1"
    _VERSION = b"\x01"
    _SIGN_MAGIC = b"SIGN"
    _SIGN_VERSION = b"\x01"

    def __init__(self, key_dir=None, PIN="toolsbox"):
        self._PIN = PIN
        self._key_dir = None

        if key_dir is not None:
            self.set_key_dir(key_dir)

    def set_key_dir(self, key_dir):
        """
        切换 / 设置密钥目录
        """
        self._key_dir = Path(key_dir)
        self._key_dir.mkdir(parents=True, exist_ok=True)

        self._crypt_key_path = self._key_dir / "crypt_key.pem"
        self._crypt_pub_path = self._key_dir / "crypt_pub.pem"
        self._sign_key_path = self._key_dir / "sign_key.pem"
        self._sign_pub_path = self._key_dir / "sign_pub.pem"
        
    # -----------------------------------------
    #      密钥生成 / 保存 / 加载
    # -----------------------------------------
    def generate_keys(self):

        """ X25519与Ed25519公私钥对生成 """
        crypt_key = x25519.X25519PrivateKey.generate()
        crypt_pub = crypt_key.public_key()
        # Ed25519公私钥对生成 
        sign_key = ed25519.Ed25519PrivateKey.generate()
        sign_pub  = sign_key.public_key()
        if self._key_dir:
            self._save_keypair(crypt_key, crypt_pub, sign_key, sign_pub)
        return crypt_key, crypt_pub, sign_key, sign_pub

    # -----------------------------------------
    def _save_keypair(self, crypt_key, crypt_pub, sign_key, sign_pub):
        """保存密钥对为 PEM 文件"""

        pin = self._PIN
        enc = (
            serialization.BestAvailableEncryption(pin.encode())
            if pin else serialization.NoEncryption()
        )
        with open(self._crypt_key_path, "wb") as f:
            f.write(crypt_key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                enc
            ))
        with open(self._crypt_pub_path, "wb") as f:
            f.write(crypt_pub.public_bytes(
                serialization.Encoding.PEM,
                serialization.PublicFormat.SubjectPublicKeyInfo
            ))
        with open(self._sign_key_path, "wb") as f:
            f.write(sign_key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                enc
            ))
        with open(self._sign_pub_path, "wb") as f:
            f.write(sign_pub.public_bytes(
                serialization.Encoding.PEM,
                serialization.PublicFormat.SubjectPublicKeyInfo
            ))

    # -----------------------------------------
    def _load_keypair(self):
        """加载私钥和公钥"""
        if not all(p.exists() for p in (
                self._crypt_key_path,
                self._crypt_pub_path,
                self._sign_key_path,
                self._sign_pub_path
            )):
            print("密钥文件不存在")
            return None, None, None, None

        pwd = self._PIN.encode()

        try:
            with open(self._crypt_key_path, "rb") as f:
                crypt_key = serialization.load_pem_private_key(f.read(), password=pwd)
            with open(self._crypt_pub_path, "rb") as f:
                crypt_pub = serialization.load_pem_public_key(f.read())
            with open(self._sign_key_path, "rb") as f:
                sign_key = serialization.load_pem_private_key(f.read(), password=pwd)
            with open(self._sign_pub_path, "rb") as f:
                sign_pub = serialization.load_pem_public_key(f.read())
            return crypt_key, crypt_pub, sign_key, sign_pub
        except Exception as e:
            raise RuntimeError(f"加载密钥失败: {e}")

    # ============================================
    #  混合加密（ECC + AEAD）
    #  text → 加密 → dict
    # ============================================

    def encrypt(self, data=None, pubkey=None,data_path=None,save="off") -> bytes:
        """
        参数：
            data: str | bytes | data_path
            pubkey: 公钥（X25519）
            data_path: 数据文件路径（可选）
            save: 为空时不保存。否则保存到data_path同名.enc文件或者指定文件路径

        返回：
            bytes: 二进制数据包
        """

        if pubkey is None and self._key_dir is not None:
            _, pubkey, _, _ = self._load_keypair()
        if pubkey is None and self._key_dir is None:
            raise ValueError("未提供公钥，且未指定密钥目录")
        if data is None and data_path is None:
            raise ValueError("必须提供数据或数据路径")
        if not isinstance(pubkey, X25519PublicKey):
            raise TypeError("pubkey 必须是 X25519 公钥")

        if data_path is not None:
            path = Path(data_path)
            data = path.read_bytes()

        # ✅ 统一转 bytes
        if isinstance(data, str):
            plaintext = self._TYPE_TEXT+data.encode("utf-8")
        elif isinstance(data, bytes):
            plaintext = self._TYPE_BYTES+data
        else:
            raise TypeError("加密数据必须是 str 或 bytes")
        
        # 成一次性密钥（前向安全）
        eph_priv = x25519.X25519PrivateKey.generate()
        eph_pub = eph_priv.public_key()

        # ECDH 计算共享密钥
        shared_key = eph_priv.exchange(pubkey)

        key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self._MAGIC + self._VERSION,
            info=b"SIMPLE-ECC",
        ).derive(shared_key)

        # ChaCha20-Poly1305 加密（带认证）
        nonce = os.urandom(12)

        eph_pub_bytes = eph_pub.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        aad = self._MAGIC + self._VERSION + eph_pub_bytes
        
        ciphertext = ChaCha20Poly1305(key).encrypt(
            nonce,
            plaintext,
            aad
        )

        packet = (
            self._MAGIC +
            self._VERSION +
            eph_pub_bytes +
            nonce +
            ciphertext
        )
        # ===== 保存文件 =====
        if save != 'off':
            if data_path is not None:
                if save == 'on':
                    out_path = path.with_suffix(path.suffix + ".enc")
                else:
                    out_path = save
            else:
                if save == 'on':
                    out_path = Path.cwd() / "encrypt_output.enc"
                else:
                    out_path = save
            out_path = Path(out_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)

            with open(out_path, "wb") as f:
                f.write(packet)

        return packet
    
    # ============================================
    #  解密流程：ECC → AEAD → text
    def decrypt(self, packet: bytes = None, privkey=None, enc_data_path=None, save="off"):
        """
        参数：
            packet (bytes): get_encrypt() 返回的数据
            privkey: 私钥（X25519）
            enc_data_path: .enc 文件路径（可选）
            save: 保存文件名（不含后缀）；若 enc_data_path 存在则自动去掉 .enc
        返回：
            str | bytes
        """
        if privkey is None and self._key_dir is not None:
            privkey, _, _, _ = self._load_keypair()
        if privkey is None and self._key_dir is None:
            raise ValueError("未提供私钥，且未指定密钥目录")

        if packet is None and enc_data_path is None:
            raise ValueError("必须提供 packet 或 enc_data_path")

        # ✅ 从文件读取
        if enc_data_path is not None:
            path = Path(enc_data_path)
            packet = path.read_bytes()

        try:
            # ===== 解析头部 =====
            if len(packet) < 4 + 1 + 32 + 12:
                raise ValueError("数据长度不合法")

            magic = packet[:4]
            version = packet[4]

            if magic != self._MAGIC:
                raise ValueError("未知数据格式")
            if version != self._VERSION[0]:
                raise ValueError(f"不支持的版本: {version}")

            offset = 5
            eph_pub_bytes = packet[offset:offset + 32]
            offset += 32
            nonce = packet[offset:offset + 12]
            offset += 12
            ciphertext = packet[offset:]

            eph_pub = x25519.X25519PublicKey.from_public_bytes(eph_pub_bytes)

            # ===== ECDH + HKDF =====
            shared_key = privkey.exchange(eph_pub)

            key = HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=self._MAGIC + self._VERSION,
                info=b"SIMPLE-ECC",
            ).derive(shared_key)

            aad = self._MAGIC + self._VERSION + eph_pub_bytes
            plaintext = ChaCha20Poly1305(key).decrypt(nonce, ciphertext, aad)

            # ===== 解包 =====
            if not plaintext:
                raise ValueError("空明文")

            t = plaintext[0:1]
            body = plaintext[1:]
            if t == self._TYPE_TEXT:
                result = body.decode("utf-8")
                ext = ".txt"
                out_data = body
            elif t == self._TYPE_BYTES:
                result = body
                ext = ""
                out_data = body
            else:
                raise ValueError("未知明文类型")

            # ===== 保存文件 =====

            # ===== 保存文件 =====
            if save != 'off':
                if enc_data_path is not None:
                    orig_path = path.with_suffix("")  # 去掉 .enc
                    if save == 'on':
                        # 原文件名 + _decrypt + 原后缀
                        out_path = orig_path.with_name(
                            f"{orig_path.stem}_decrypt{orig_path.suffix}"
                        )
                    else:
                        out_path = save
                else:
                    if save == 'on':
                        out_path = Path.cwd() / "decrypt_output.bin"
                    else:
                        out_path = save
                out_path = Path(out_path)
                out_path.parent.mkdir(parents=True, exist_ok=True)

                with open(out_path, "wb") as f:
                    f.write(out_data)

            return result

        except Exception as e:
            print("解密失败:", e)
            return None
        
    # ============================================
    #  数字签名与验签功能（Ed25519）
    # ============================================
    def sign(self, data=None, sign_key=None, data_path=None, save="off"):
        """
        使用 Ed25519 对数据进行数字签名，并生成自描述的签名数据包。

        参数：
            data (str | bytes | None): 待签名的数据内容。

            sign_key (ed25519.Ed25519PrivateKey | None): 可选密钥

            data_path (str | Path | None): 可选待签名文件的路径（覆盖data）

            save (str): 控制是否将签名数据包保存为文件。"off"（默认）

        返回：
            bytes: 签名数据包（二进制格式），结构如下：

        """
        if sign_key is None and self._key_dir is not None:
            _, _, sign_key, _ = self._load_keypair()
        
        if sign_key is None and self._key_dir is None:
            raise ValueError("未提供签名私钥，且未指定密钥目录")
        if data is None and data_path is None:
            raise ValueError("必须提供 data 或 data_path")

        # ===== 读取数据 =====
        if data_path is not None:
            path = Path(data_path)
            payload = path.read_bytes()      # ✅ 文件永远按 bytes
            t = self._TYPE_BYTES
        else:
            if isinstance(data, str):
                payload = data.encode("utf-8")
                t = self._TYPE_TEXT
            elif isinstance(data, bytes):
                payload = data
                t = self._TYPE_BYTES
            else:
                raise TypeError("签名数据必须是 str 或 bytes")

        body = t + payload

        # ===== Ed25519 签名 =====
        sig = sign_key.sign(body)

        packet = (
            self._SIGN_MAGIC +
            self._SIGN_VERSION +
            body +
            sig
        )

        # ===== 保存签名文件 =====
        if save != 'off':
            if data_path is not None:
                # 自动生成：原名 + _signed + 原后缀
                if save == 'on':
                    out_path = path.with_name(
                        f"{path.stem}_signed{path.suffix}"
                    )
                else: out_path = save
            else:
                if save == 'on':
                    out_path = Path.cwd() / "signed_output.bin"
                else:
                    out_path = save
                
            out_path = Path(out_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)

            # ===== 写入签名包 =====
            with open(out_path, "wb") as f:
                f.write(packet)

        return packet

    # --------------------------------------------
    def verify(self, signed_data=None, verify_key=None, signed_data_path=None, save="off"):
        """
        验证 Ed25519 签名

        参数:
            signed_data:
                - bytes            : 签名数据包
                - str (base64)     : 签名数据包
            signed_data_path:
                - None             : 从签名包验签
                - 文件路径(str)    : 对指定文件验签

        返回：
            - str          : 验签成功并还原文本数据
            - None         : 验签失败
        """
        if verify_key is None and self._key_dir is not None:
            _, _, _, verify_key = self._load_keypair()
        if verify_key is None and self._key_dir is None:
            raise ValueError("未提供验签公钥，且未指定密钥目录")

        try:
            # ===== 文件验签模式 =====
            if signed_data_path is not None:
                path = Path(signed_data_path)
                packet = path.read_bytes()

            # ===== 传输层解码 =====
            else:
                if isinstance(signed_data, str):
                    import base64
                    packet = base64.b64decode(signed_data.encode("ascii"))
                elif isinstance(signed_data, bytes):
                    packet = signed_data
                else:
                    raise TypeError("验签数据必须是 str 或 bytes")

            # ===== 基本校验 =====
            if len(packet) < 4 + 1 + 1 + self._SIGN_LEN:
                raise ValueError("签名数据长度不合法")

            magic = packet[:4]
            version = packet[4]

            if magic != self._SIGN_MAGIC:
                raise ValueError("未知签名格式")
            if version != self._SIGN_VERSION[0]:
                raise ValueError("不支持的签名版本")

            offset = 5
            t = packet[offset:offset + 1]
            offset += 1

            payload = packet[offset:-self._SIGN_LEN]
            sig = packet[-self._SIGN_LEN:]

            # ===== 数据验签模式 =====
            verify_key.verify(sig, t + payload)

            # ===== 保存文件 =====
            if save != 'off':
                if signed_data_path is not None:
                    # 自动生成：原名 + _verify + 原后缀
                    if save == 'on':
                        out_path = path.with_name(
                            f"{path.stem}_verify{path.suffix}"
                        )
                    else: out_path = save
                else:
                    if save == 'on':
                        out_path = Path.cwd() / "verify_output.bin"
                    else:
                        out_path = save
                    
                out_path = Path(out_path)
                out_path.parent.mkdir(parents=True, exist_ok=True)

                # ===== 写入签名包 =====
                with open(out_path, "wb") as f:
                    f.write(payload)


            #   还原数据，根据类型返回str或bytes    
            if t == self._TYPE_TEXT:
                return payload.decode("utf-8")
            elif t == self._TYPE_BYTES:
                return payload
            else:
                raise ValueError("未知数据类型")

        except Exception as e:
            print("验签失败:", e)
            return None




if __name__ == "__main__":

    from raytoolsbox import useful_func
    tt=useful_func.make_timer()

    test_data_dir = Path("tests/testData")
    if not test_data_dir.exists():
        test_data_dir.mkdir(parents=True, exist_ok=True)
    with open(test_data_dir / "测试文档.txt", "r", encoding="utf-8") as f:
        plaintext0 = f.read()
    tt()
    cm = CryptoManager(test_data_dir / "ecc_keys")
    priv, pub,_,_ = cm.generate_keypair()
    tt("密钥对生成完成")
    js=cm.get_encrypt(plaintext0, pub)
    tt("加密完成")
    plaintext = cm.get_decrypt(js, priv)
    if plaintext==plaintext0:
        print("解密成功，内容一致")
    tt("解密完成")
    # 写到文件
    with open(test_data_dir / "test_decrypt.txt", "w", encoding="utf-8") as f:
        f.write(plaintext)
    tt()