import base64
import gzip
import hashlib
import hmac
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
from Crypto.Cipher import AES, DES, PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad

SKLAND_SM_CONFIG = {
    "organization": "UWXspnCCJN4sfYlNfqps",
    "appId": "default",
    "publicKey": "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCmxMNr7n8ZeT0tE1R9j/"
    "mPixoinPkeM+k4VGIn/s0k7N5rJAfnZ0eMER+QhwFvshzo0LNmeUkpR8uI"
    "lU/GEVr8mN28sKmwd2gpygqj0ePnBmOW4v0ZVwbSYK+izkhVFk2V/doLoM"
    "bWy6b+UnA8mkjvg0iYWRByfRsK2gdl7llqCwIDAQAB",
    "protocol": "https",
    "apiHost": "fp-it.portal101.cn",
    "apiPath": "/deviceprofile/v4",
}

DES_RULE: dict[str, dict[str, Any]] = {
    "appId": {"cipher": "DES", "is_encrypt": 1, "key": "uy7mzc4h", "obfuscated_name": "xx"},
    "box": {"is_encrypt": 0, "obfuscated_name": "jf"},
    "canvas": {"cipher": "DES", "is_encrypt": 1, "key": "snrn887t", "obfuscated_name": "yk"},
    "clientSize": {"cipher": "DES", "is_encrypt": 1, "key": "cpmjjgsu", "obfuscated_name": "zx"},
    "organization": {
        "cipher": "DES",
        "is_encrypt": 1,
        "key": "78moqjfc",
        "obfuscated_name": "dp",
    },
    "os": {"cipher": "DES", "is_encrypt": 1, "key": "je6vk6t4", "obfuscated_name": "pj"},
    "platform": {"cipher": "DES", "is_encrypt": 1, "key": "pakxhcd2", "obfuscated_name": "gm"},
    "plugins": {"cipher": "DES", "is_encrypt": 1, "key": "v51m3pzl", "obfuscated_name": "kq"},
    "pmf": {"cipher": "DES", "is_encrypt": 1, "key": "2mdeslu3", "obfuscated_name": "vw"},
    "protocol": {"is_encrypt": 0, "obfuscated_name": "protocol"},
    "referer": {"cipher": "DES", "is_encrypt": 1, "key": "y7bmrjlc", "obfuscated_name": "ab"},
    "res": {"cipher": "DES", "is_encrypt": 1, "key": "whxqm2a7", "obfuscated_name": "hf"},
    "rtype": {"cipher": "DES", "is_encrypt": 1, "key": "x8o2h2bl", "obfuscated_name": "lo"},
    "sdkver": {"cipher": "DES", "is_encrypt": 1, "key": "9q3dcxp2", "obfuscated_name": "sc"},
    "status": {"cipher": "DES", "is_encrypt": 1, "key": "2jbrxxw4", "obfuscated_name": "an"},
    "subVersion": {"cipher": "DES", "is_encrypt": 1, "key": "eo3i2puh", "obfuscated_name": "ns"},
    "svm": {"cipher": "DES", "is_encrypt": 1, "key": "fzj3kaeh", "obfuscated_name": "qr"},
    "time": {"cipher": "DES", "is_encrypt": 1, "key": "q2t3odsk", "obfuscated_name": "nb"},
    "timezone": {"cipher": "DES", "is_encrypt": 1, "key": "1uv05lj5", "obfuscated_name": "as"},
    "tn": {"cipher": "DES", "is_encrypt": 1, "key": "x9nzj1bp", "obfuscated_name": "py"},
    "trees": {"cipher": "DES", "is_encrypt": 1, "key": "acfs0xo4", "obfuscated_name": "pi"},
    "ua": {"cipher": "DES", "is_encrypt": 1, "key": "k92crp1t", "obfuscated_name": "bj"},
    "url": {"cipher": "DES", "is_encrypt": 1, "key": "y95hjkoo", "obfuscated_name": "cf"},
    "version": {"is_encrypt": 0, "obfuscated_name": "version"},
    "vpw": {"cipher": "DES", "is_encrypt": 1, "key": "r9924ab5", "obfuscated_name": "ca"},
}

BROWSER_ENV: dict[str, Any] = {
    "plugins": "MicrosoftEdgePDFPluginPortableDocumentFormatinternal-pdf-viewer1,MicrosoftEdgePDFViewermhjfbmdgcfjbbpaeojofohoefgiehjai1",  # noqa: E501
    "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",  # noqa: E501
    "canvas": "259ffe69",
    "timezone": -480,
    "platform": "Win32",
    "url": "https://www.skland.com/",
    "referer": "",
    "res": "1920_1080_24_1.25",
    "clientSize": "0_0_1080_1920_1920_1080_1920_1080",
    "status": "0011",
}

DEVICES_INFO_URL = (
    f"{SKLAND_SM_CONFIG['protocol']}://{SKLAND_SM_CONFIG['apiHost']}{SKLAND_SM_CONFIG['apiPath']}"
)
MILLISECOND_PER_SECOND = 1000


def md5_hex(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest()


def hmac_sha256_hex(key: str, data: str) -> str:
    return hmac.new(key.encode(), data.encode(), hashlib.sha256).hexdigest()


def aes_cbc_hex(plaintext: str, key16: str) -> str:
    """等价于 TS encryptAES：AES-CBC + 固定 IV('0102030405060708') → hex"""
    iv = b"0102030405060708"  # 16 字节 ASCII
    cipher = AES.new(key16.encode(), AES.MODE_CBC, iv=iv)
    ct = cipher.encrypt(pad(plaintext.encode(), AES.block_size))
    return ct.hex()


def des_ecb_b64_zero_pad(plaintext: str, key8: str) -> str:
    """等同 TS encryptDES：手动 0x00 填充 + DES-ECB → Base64"""
    bs = 8
    padded = plaintext.encode() + b"\x00" * (bs - len(plaintext.encode()) % bs)
    cipher = DES.new(key8.encode(), DES.MODE_ECB)
    ct = cipher.encrypt(padded)
    return base64.b64encode(ct).decode()


def rsa_pkcs1_b64(plaintext: str, pubkey_b64: str) -> str:
    """PKCS#1 v1.5 加密（与 mima.pkcs1_es_1_5 一致）"""
    key = RSA.import_key(base64.b64decode(pubkey_b64))
    cipher = PKCS1_v1_5.new(key)
    ct = cipher.encrypt(plaintext.encode())
    return base64.b64encode(ct).decode()


def gzip_b64(obj: dict[str, Any]) -> str:
    """按 TS gzipObject：JSON + 插空格 + gzip + 改 OS flag → Base64"""
    json_str = json.dumps(obj).replace('":"', '": "').replace('","', '", "')
    gz = gzip.compress(json_str.encode())
    ba = bytearray(gz)
    if len(ba) > 9:  # 改 OS flag = 19 (unknown)
        ba[9] = 19
    return base64.b64encode(ba).decode()


def get_sm_id() -> str:
    now = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    uid = str(uuid.uuid4())
    v = f"{now}{md5_hex(uid)}00"
    smsk_web = md5_hex(f"smsk_web_{v}")[:14]
    return f"{v}{smsk_web}0"


def get_tn(o: dict[str, Any]) -> str:
    parts = []
    for k in sorted(o.keys()):
        v = o[k]
        if isinstance(v, int | float):
            v = str(int(v) * 10000)
        elif isinstance(v, dict):
            v = get_tn(v)
        parts.append(str(v))
    return "".join(parts)


def encrypt_object_by_des_rules(
    data: dict[str, Any], rules: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    """按 DES_RULE 混淆 & 加密字段"""
    out: dict[str, Any] = {}
    for k, rule in rules.items():
        if k not in data:
            continue
        ob_name = rule["obfuscated_name"]
        val = data[k]
        if rule.get("is_encrypt") == 1 and rule.get("cipher") == "DES":
            val = des_ecb_b64_zero_pad(str(val), rule["key"])
        out[ob_name] = val
    return out


async def getDid() -> str:
    uid = str(uuid.uuid4())
    pri_id = md5_hex(uid)[:16]  # 16-hex → 16 ASCII bytes
    ep = rsa_pkcs1_b64(uid, SKLAND_SM_CONFIG["publicKey"])

    browser = {
        **BROWSER_ENV,
        "vpw": str(uuid.uuid4()),
        "svm": int(time.time() * MILLISECOND_PER_SECOND),
        "trees": str(uuid.uuid4()),
        "pmf": int(time.time() * MILLISECOND_PER_SECOND),
    }

    des_target: dict[str, Any] = {
        **browser,
        "protocol": 102,
        "organization": SKLAND_SM_CONFIG["organization"],
        "appId": SKLAND_SM_CONFIG["appId"],
        "os": "web",
        "version": "3.0.0",
        "sdkver": "3.0.0",
        "box": "",
        "rtype": "all",
        "smid": get_sm_id(),
        "subVersion": "1.0.0",
        "time": 0,
    }
    des_target["tn"] = md5_hex(get_tn(des_target))

    des_result = encrypt_object_by_des_rules(des_target, DES_RULE)
    gzip_result = gzip_b64(des_result)  # 已是 Base64 字符串
    aes_result = aes_cbc_hex(gzip_result, pri_id)  # 输出 hex 字符串

    body = {
        "appId": "default",
        "compress": 2,
        "data": aes_result,
        "encode": 5,
        "ep": ep,
        "organization": SKLAND_SM_CONFIG["organization"],
        "os": "web",
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(DEVICES_INFO_URL, json=body)
        resp.raise_for_status()
    resp_json = resp.json()
    if resp_json.get("code") != 1100:
        raise ValueError(f"DID 计算失败: {resp_json}")
    return "B" + resp_json["detail"]["deviceId"]
