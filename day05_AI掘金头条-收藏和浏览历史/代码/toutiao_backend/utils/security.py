"""密码哈希。

原代码用 passlib 的 CryptContext,但 passlib 最后一个版本停在 2020 年,
读不到 bcrypt 4.1 以后删掉的 __about__ 属性,后端初始化直接失败,
注册接口报 500:

    AttributeError: module 'bcrypt' has no attribute '__about__'
    ValueError: password cannot be longer than 72 bytes

passlib 官方也已经建议直接使用 bcrypt。所以这里改用 bcrypt 库实现,
函数名(get_hash_password / verify_password)和用法完全不变,调用方一行都不用改。
"""

import bcrypt

# bcrypt 算法本身只取前 72 字节,新版库遇到超长密码会直接抛错,所以要自己截断
MAX_PASSWORD_BYTES = 72


def _to_bytes(password: str) -> bytes:
    return password.encode("utf-8")[:MAX_PASSWORD_BYTES]


def get_hash_password(password: str) -> str:
    """把明文密码转成哈希值存库。盐由 bcrypt 随机生成,同样的密码每次结果都不同。"""
    return bcrypt.hashpw(_to_bytes(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password, hashed_password) -> bool:
    """校验密码。checkpw 内部是常量时间比较,能防时序攻击,不用手写比较。"""
    try:
        return bcrypt.checkpw(_to_bytes(plain_password), hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        # 库里存的不是合法 bcrypt 哈希(比如历史脏数据),一律当作校验失败
        return False
