import base64
import os

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


class AESCrypto:
    """AES加解密工具类，与前端CryptoJS对应"""

    @staticmethod
    def aes_encode(data: str, key_code: str) -> str:
        """
        AES加密，对应前端的aesEncode函数
        :param data: 要加密的字符串
        :param key_code: 密钥，必须是16、24或32位长
        :return: 加密后的字符串，格式为IV:密文
        """
        # 验证密钥长度
        if len(key_code) not in [16, 24, 32]:
            raise ValueError("AES密钥长度必须为16、24或32位")

        try:
            # 将密钥转换为bytes
            key = key_code.encode("utf-8")

            # 生成随机的16字节IV
            iv = os.urandom(16)

            # 创建AES加密器，使用CBC模式和PKCS7填充
            cipher = AES.new(key, AES.MODE_CBC, iv)

            # 对数据进行填充并加密
            padded_data = pad(data.encode("utf-8"), AES.block_size)
            encrypted_data = cipher.encrypt(padded_data)

            # 将IV转换为十六进制字符串，并与base64编码的密文拼接
            iv_hex = iv.hex()
            encrypted_base64 = base64.b64encode(encrypted_data).decode("utf-8")

            return f"{iv_hex}:{encrypted_base64}"

        except Exception as e:
            raise Exception(f"AES加密失败: {str(e)}")

    @staticmethod
    def aes_decode(encrypted_str: str, key_code: str) -> str:
        """
        AES解密，对应前端的aesDecode函数
        :param encrypted_str: 加密后的字符串，格式为IV:密文
        :param key_code: 密钥，必须是16、24或32位长
        :return: 解密后的原始字符串
        """
        # 验证密钥长度
        if len(key_code) not in [16, 24, 32]:
            raise ValueError("AES密钥长度必须为16、24或32位")

        try:
            # 分割IV和密文
            parts = encrypted_str.split(":", 1)
            if len(parts) != 2:
                raise ValueError("解密数据格式不正确，应为IV:密文格式")

            # 解析IV和密文
            iv_hex = parts[0]
            encrypted_base64 = parts[1]

            # 将IV从十六进制转换为bytes
            iv = bytes.fromhex(iv_hex)

            # 将密钥转换为bytes
            key = key_code.encode("utf-8")

            # 解码base64密文
            encrypted_data = base64.b64decode(encrypted_base64)

            # 创建AES解密器
            cipher = AES.new(key, AES.MODE_CBC, iv)

            # 解密并去除填充
            decrypted_padded = cipher.decrypt(encrypted_data)
            decrypted_data = unpad(decrypted_padded, AES.block_size)

            # 返回解密后的字符串
            return decrypted_data.decode("utf-8")

        except Exception as e:
            raise Exception(f"AES解密失败: {str(e)}")


# 提供便捷的函数接口，与前端函数名对应
def aes_encode(data: str, key_code: str) -> str:
    """AES加密函数"""
    return AESCrypto.aes_encode(data, key_code)


def aes_decode(encrypted_str: str, key_code: str) -> str:
    """AES解密函数"""
    return AESCrypto.aes_decode(encrypted_str, key_code)


# 示例用法
if __name__ == "__main__":
    try:
        # 测试密钥(16位)
        key = "kalarda@#.com8la"

        # 测试数据
        original_text = "Admin"
        print(f"原始数据: {original_text}")

        # 加密
        encrypted = aes_encode(original_text, key)
        print(f"加密后: {encrypted}")

        # 解密
        decrypted = aes_decode(encrypted, key)
        print(f"解密后: {decrypted}")

        # 验证解密是否正确
        assert original_text == decrypted, "解密结果与原始数据不一致"
        print("测试成功: 加密解密功能正常")

    except Exception as e:
        print(f"测试失败: {str(e)}")
