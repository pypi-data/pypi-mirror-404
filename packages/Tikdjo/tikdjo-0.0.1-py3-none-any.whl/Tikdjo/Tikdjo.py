from random import randint
from struct import unpack
from base64 import b64encode
from hashlib import md5
from urllib.parse import parse_qs
from Crypto.Cipher.AES import new, MODE_CBC, block_size
from Crypto.Util.Padding import pad
from Crypto.Cipher.AES import new, MODE_CBC, block_size
from ctypes import c_ulonglong
from enum import IntEnum, unique
import hashlib
import random
from urllib.parse import urlencode
from typing import Optional, Union
import base64
import hashlib
import ctypes
from os import urandom
from random import choice
from urllib.parse import urlencode
from typing import Union
import hmac, uuid, random, binascii, os, secrets, time, hashlib, string
import time
import secrets
import string
import hashlib
import random
import uuid
import binascii
import os
import hmac
from typing import Optional, Union, Dict, Any
from urllib.parse import urlencode, urlparse, parse_qsl
import random, string

def random_hex(length=8):
    return ''.join(random.choice('0123456789abcdef') for _ in range(length))

def UserAgentTik(params=None):
    device_types = {        
        "Samsung": [
            "Galaxy S24 Ultra", "Galaxy S24+", "Galaxy S24", "Galaxy S23 Ultra", "Galaxy S23", "Galaxy S22 Ultra",
            "Galaxy Z Fold 6", "Galaxy Z Fold 5", "Galaxy Z Flip 6", "Galaxy Z Flip 5",
            "Galaxy Note 20 Ultra", "Galaxy A74", "Galaxy A73", "Galaxy A54", "Galaxy A34",
            "Galaxy M54", "Galaxy M14", "Galaxy S21 FE", "Galaxy A14", "Galaxy A04s"
        ],
        "Xiaomi": [
            "14 Ultra", "14 Pro", "14", "13T Pro", "13 Ultra", "13", "12 Pro", "12T", "Mi 11", "Mi 10T Pro",
            "Redmi Note 13 Pro+", "Redmi Note 13 Pro", "Redmi Note 12 Pro", "Redmi Note 11 Pro", "POCO F5", 
            "POCO X5 Pro", "POCO X4 GT", "Redmi K60 Pro", "Redmi K50", "POCO M6 Pro"
        ],
        "Huawei": [
            "P60 Pro", "P50 Pro", "P40 Pro", "Mate 60 Pro+", "Mate 60", "Mate 50", "Nova 12 Pro", "Nova 11i",
            "Nova 10 SE", "Nova 9", "Y9a", "Y70", "P Smart 2023", "Y6p"
        ],
        "Honor": [
            "Magic 6 Pro", "Magic 5 Pro", "Magic 4 Pro", "Magic V2", "Magic Vs", "Honor 90", "Honor 70", "Honor X9a",
            "Honor X8b", "Honor 50", "Honor Play 40", "Honor Play 30"
        ],
        "Google": [
            "Pixel 9 Pro", "Pixel 8 Pro", "Pixel 8", "Pixel 7a", "Pixel 7", "Pixel 6a", "Pixel 6 Pro", "Pixel 5"
        ],
        "OnePlus": [
            "12R", "12", "11", "10T", "10 Pro", "9 Pro", "9", "8T", "Nord 3", "Nord 2T", "Nord CE 3"
        ],
        "Oppo": [
            "Find X7 Ultra", "Find X6 Pro", "Find X5 Pro", "Reno 11 Pro", "Reno 10 Pro", "Reno 8 Pro",
            "A98", "A78", "A58", "A57", "A17", "F23", "F21 Pro"
        ],
        "Realme": [
            "GT 5 Pro", "GT 3", "GT 2 Pro", "11 Pro+", "10 Pro+", "9 Pro+", "C67", "C53", "Narzo 60", "Narzo 50"
        ],
        "Vivo": [
            "X100 Pro", "X100", "X90 Pro+", "V29 Pro", "V27", "V25e", "Y100", "Y78", "Y56", "Y36", "T2 Pro"
        ],
        "Sony": [
            "Xperia 1 VI", "Xperia 1 V", "Xperia 5 V", "Xperia 10 V", "Xperia 5 IV", "Xperia 10 IV"
        ],
        "Motorola": [
            "Edge 50 Ultra", "Edge 40 Neo", "Edge 30 Ultra", "Moto G84", "Moto G73", "Moto G23", "Moto E13", "Razr 40 Ultra"
        ],
        "Nokia": [
            "G60", "X30", "X20", "G50", "G42", "C32", "C22", "G11 Plus", "C21"
        ],
        "Asus": [
            "ROG Phone 8", "ROG Phone 7 Ultimate", "Zenfone 10", "Zenfone 9", "ROG Phone 6 Pro"
        ],
        "Infinix": [
            "Zero 30 5G", "Zero 20", "Note 30 VIP", "Note 30 Pro", "Hot 40 Pro", "Hot 30", "Smart 8"
        ],
        "Tecno": [
            "Phantom X2 Pro", "Camon 30 Premier", "Camon 20 Pro", "Spark 20 Pro", "Pova 5", "Pop 8"
        ],
        "Lenovo": [
            "Legion Y90", "Legion Duel 2", "K14 Plus", "Tab M10", "Tab P12 Pro"
        ],
        "ZTE": [
            "Axon 50 Ultra", "Axon 40 Ultra", "Blade V50", "Blade A73", "Libero 5G IV"
        ],
        "Meizu": [
            "21 Pro", "20 Pro", "18s Pro", "18X", "Note 9"
        ]
    }

    brand = random.choice(list(device_types.keys()))
    device_type = random.choice(device_types[brand])
    if params is None:
        params = {}

    version_code = params.get("manifest_version_code") or params.get("update_version_code") or str(random.randint(2023000000, 2024999999))
    ttnet_version = random_hex(8)
    quic_version = random_hex(8)

    agent = (
        f"com.zhiliaoapp.musically/{version_code} "
        f"(Linux; U; Android {random.randint(10,14)}; ar_YE; {device_type}; "
        f"Build/{brand}{random.choice(string.ascii_uppercase)}{random.randint(100,999)}; "
        f"Cronet/TTNetVersion:{ttnet_version} 2024-{random.randint(1,12):02d}-{random.randint(1,28):02d} "
        f"QuicVersion:{quic_version} 2024-{random.randint(1,12):02d}-{random.randint(1,28):02d})"
    )

    return {
        'brand': brand,
        'type': device_type,
        'User-Agent': agent
    }




def md5bytes(data: bytes) -> str:
    m = hashlib.md5()
    m.update(data)
    return m.hexdigest()

def get_type_data(ptr, index, data_type):
    if data_type == "uint64_t":
        return int.from_bytes(ptr[index * 8 : (index + 1) * 8], "little")
    else:
        raise ValueError("Invalid data type")

def set_type_data(ptr, index, data, data_type):
    if data_type == "uint64_t":
        ptr[index * 8 : (index + 1) * 8] = data.to_bytes(8, "little")
    else:
        raise ValueError("Invalid data type")

def validate(num):
    return num & 0xFFFFFFFFFFFFFFFF

def __ROR__(value: ctypes.c_ulonglong, count: int) -> ctypes.c_ulonglong:
    nbits = ctypes.sizeof(value) * 8
    count %= nbits
    low = ctypes.c_ulonglong(value.value << (nbits - count)).value
    value = ctypes.c_ulonglong(value.value >> count).value
    value = value | low
    return value

def encrypt_ladon_input(hash_table, input_data):
    data0 = int.from_bytes(input_data[:8], byteorder="little")
    data1 = int.from_bytes(input_data[8:], byteorder="little")

    for i in range(0x22):
        hash = int.from_bytes(hash_table[i * 8 : (i + 1) * 8], byteorder="little")
        data1 = validate(hash ^ (data0 + ((data1 >> 8) | (data1 << (64 - 8)))))
        data0 = validate(data1 ^ ((data0 >> 0x3D) | (data0 << (64 - 0x3D))))

    output_data = bytearray(16)
    output_data[:8] = data0.to_bytes(8, byteorder="little")
    output_data[8:] = data1.to_bytes(8, byteorder="little")

    return bytes(output_data)

def encrypt_ladon(md5hex: bytes, data: bytes, size: int):
    hash_table = bytearray(272 + 16)
    hash_table[:32] = md5hex

    temp = []
    for i in range(4):
        temp.append(int.from_bytes(hash_table[i * 8 : (i + 1) * 8], byteorder="little"))

    buffer_b0 = temp[0]
    buffer_b8 = temp[1]
    temp.pop(0)
    temp.pop(0)

    for i in range(0, 0x22):
        x9 = buffer_b0
        x8 = buffer_b8
        x8 = validate(__ROR__(ctypes.c_ulonglong(x8), 8))
        x8 = validate(x8 + x9)
        x8 = validate(x8 ^ i)
        temp.append(x8)
        x8 = validate(x8 ^ __ROR__(ctypes.c_ulonglong(x9), 61))
        set_type_data(hash_table, i + 1, x8, "uint64_t")
        buffer_b0 = x8
        buffer_b8 = temp[0]
        temp.pop(0)

    def padding_size(size: int) -> int:
        mod = size % 16
        if mod > 0:
            return size + (16 - mod)
        return size

    def pkcs7_padding_pad_buffer(buffer: bytearray, data_length: int, buffer_size: int, modulus: int) -> int:
        pad_byte = modulus - (data_length % modulus)
        if data_length + pad_byte > buffer_size:
            return -pad_byte
        for i in range(pad_byte):
            buffer[data_length+i] = pad_byte
        return pad_byte

    new_size = padding_size(size)

    input = bytearray(new_size)
    input[:size] = data
    pkcs7_padding_pad_buffer(input, size, new_size, 16)

    output = bytearray(new_size)
    for i in range(new_size // 16):
        output[i * 16 : (i + 1) * 16] = encrypt_ladon_input(
            hash_table, input[i * 16 : (i + 1) * 16]
        )

    return output

def ladon_encrypt(
    khronos: int,
    lc_id: int = 1611921764,
    aid: int = 1233,
    random_bytes: bytes = urandom(4)) -> str:
    
    data = f"{khronos}-{lc_id}-{aid}"

    keygen = random_bytes + str(aid).encode()
    md5hex = md5bytes(keygen)

    size = len(data)
    
    def padding_size(size: int) -> int:
        mod = size % 16
        if mod > 0:
            return size + (16 - mod)
        return size

    new_size = padding_size(size)

    output = bytearray(new_size + 4)
    output[:4] = random_bytes

    output[4:] = encrypt_ladon(md5hex.encode(), data.encode(), size)

    return base64.b64encode(bytes(output)).decode()

class Ladon:
    @staticmethod
    def encrypt(x_khronos: int, lc_id: int, aid: int) -> str:
        return ladon_encrypt(x_khronos, lc_id, aid)

#Update
class Gorgon:
    def __init__(
        self,
        params: Optional[Union[str, dict]] = None,
        unix: Optional[int] = None,
        payload: Optional[Union[str, bytes]] = None,
        cookie: Optional[str] = None,
        version: Optional[Union[int, str]] = None,
    ):
        self.params = self._rO(params)
        self.payload = self._rO(payload)
        self.cookie = self._rO(cookie)
        self.unix = int(unix) if unix is not None else int(time.time())
        if version is None:
            self.version = None
        elif isinstance(version, int):
            self.version = version
        elif isinstance(version, str):
            self.version = int(version.lstrip("0")) if version.lstrip("0") else 0
        else:
            raise ValueError("Version must be int or str")

    def _rO(self, value):
        if isinstance(value, dict):
            return urlencode(value)
        if value is None:
            return ""
        return str(value)

    def _Byt(self, v) -> bytes:
        if v is None:
            return b""
        if isinstance(v, bytes):
            return v
        return str(v).encode("utf-8")

    def _md5_hex(self, b: bytes) -> str:
        return hashlib.md5(b).hexdigest()

    def _hex_string(self, num: int) -> str:
        return hex(num)[2:].rjust(2, "0")

    def _rev(self, num: int) -> int:
        s = self._hex_string(num)
        return int(s[1:] + s[:1], 16)

    def _rbit(self, num: int) -> int:
        s = bin(num)[2:].rjust(8, "0")[::-1]
        return int(s, 2)

    
    def get_value(self):
        v = self.version
        if v == 8404:
            return self._v1("8404")
        if v == 8402:
            return self._v2("8402")
        if isinstance(v, int) and 4404 <= v <= 8000:
            Prf = f"{str(v).rjust(4,'0')}b0d3"
            return self._v3(Prf)
        if isinstance(v, int) and 404 <= v <= 4403:
            Prf = f"{str(v).rjust(4,'0')}b0d3"
            return self._v0(Prf)
        if v is None:
            return self._v3("0404b0d3")
        raise ValueError("Unsupported Gorgon version")

    
    def _v0(self, Prf):
        data_hex = self._hash_concat(self.params, self.payload, self.cookie)
        return self._encrypt_v0(data_hex, Prf=Prf)

    
    def _v1(self, Prf):
        gorgon = []
        url_md5 = self._md5_hex(self.params.encode())
        gorgon += [int(url_md5[i*2:i*2+2], 16) for i in range(4)]
        if self.payload:
            data_md5 = self._md5_hex(self.payload.encode())
            gorgon += [int(data_md5[i*2:i*2+2], 16) for i in range(4)]
        else:
            gorgon += [0]*4
        if self.cookie:
            cookie_md5 = self._md5_hex(self.cookie.encode())
            gorgon += [int(cookie_md5[i*2:i*2+2], 16) for i in range(4)]
        else:
            gorgon += [0]*4
        gorgon += [0x1,0x1,0x2,0x4]
        Khronos = hex(int(self.unix))[2:].rjust(8,'0')
        gorgon += [int(Khronos[i*2:i*2+2],16) for i in range(4)]
        xg = self._xg(gorgon, Prf)
        return {"x-ss-req-ticket": str(int(self.unix*1000)), "x-khronos": str(int(self.unix)), "x-gorgon": xg}

    def _v2(self, Prf):
        return self._encrypt_v2(Prf)

    
    def _v3(self, Prf):
        val = self._encrypt_v2(Prf)
        if Prf.startswith("04"):
            val["x-gorgon"] = val["x-gorgon"].replace("840280416000", Prf+"0000")
        return val

    
    def _hash_concat(self, params, payload, cookie):
        g = self._md5_hex(params.encode())
        g += self._md5_hex(payload.encode()) if payload else "0"*32
        g += self._md5_hex(cookie.encode()) if cookie else "0"*32
        g += "0"*32
        return g

    def _encrypt_v0(self, data_hex, Prf):
        unix = int(self.unix)
        length = 0x14
        key = [
            0xDF, 0x77, 0xB9, 0x40, 0xB9, 0x9B, 0x84, 0x83, 0xD1, 0xB9,
            0xCB, 0xD1, 0xF7, 0xC2, 0xB9, 0x85, 0xC3, 0xD0, 0xFB, 0xC3
        ]
        param_list = []
        for i in range(0, 12, 4):
            temp = data_hex[8*i: 8*(i+1)]
            for j in range(4):
                H = int(temp[j*2: (j+1)*2], 16)
                param_list.append(H)
        param_list.extend([0x0, 0x6, 0xB, 0x1C])
        H = unix & 0xFFFFFFFF
        param_list.extend([(H>>24)&0xFF,(H>>16)&0xFF,(H>>8)&0xFF,H&0xFF])
        eor_result_list = [A^B for A,B in zip(param_list,key)]
        for i in range(length):
            C = self._rev(eor_result_list[i])
            D = eor_result_list[(i+1)%length]
            E = C ^ D
            F = self._rbit(E)
            H = ((F ^ 0xFFFFFFFF) ^ length) & 0xFF
            eor_result_list[i] = H
        result = "".join(self._hex_string(p) for p in eor_result_list)
        return {"x-gorgon": Prf+result, "x-khronos": str(unix)}

    def _build_param_list_v2(self):
        param_list = []
        params_md5 = self._md5_hex(self._Byt(self.params))
        param_list += [int(params_md5[i*2:i*2+2],16) for i in range(4)]
        if self.payload:
            data_md5 = self._md5_hex(self._Byt(self.payload))
            param_list += [int(data_md5[i*2:i*2+2],16) for i in range(4)]
        else:
            param_list += [0]*4
        if self.cookie:
            cookie_md5 = self._md5_hex(self._Byt(self.cookie))
            param_list += [int(cookie_md5[i*2:i*2+2],16) for i in range(4)]
        else:
            param_list += [0]*4
        param_list += [0,6,11,28]
        H=int(self.unix)&0xFFFFFFFF
        param_list += [(H>>24)&0xFF,(H>>16)&0xFF,(H>>8)&0xFF,H&0xFF]
        return param_list

    def _encrypt_v2(self, Prf):
        length=0x14
        key=[0xDF,0x77,0xB9,0x40,0xB9,0x9B,0x84,0x83,0xD1,0xB9,
             0xCB,0xD1,0xF7,0xC2,0xB9,0x85,0xC3,0xD0,0xFB,0xC3]
        param_list=self._build_param_list_v2()
        eor_result_list=[A^B for A,B in zip(param_list,key)]
        for i in range(length):
            C=self._rev(eor_result_list[i])
            D=eor_result_list[(i+1)%length]
            E=C^D
            F=self._rbit(E)
            H=((F^0xFFFFFFFF)^length)&0xFF
            eor_result_list[i]=H
        result="".join(self._hex_string(p) for p in eor_result_list)
        return {"x-ss-req-ticket": str(int(self.unix*1000)),
                "x-khronos": str(int(self.unix)),
                "x-gorgon": f"{Prf}0000{result}"}

    def _xg(self, debug_list, Prf):
        result = ''.join(self._hex_string(d) for d in debug_list)
        hex_CE0 = [0x05,0x00,0x50,random.randrange(0,0xFF),0x47,0x1E,0x00,(random.randrange(0,0xFF)&0xF0)]
        return "{}{}{}{}{}{}".format(Prf,
                                     self._hex_string(hex_CE0[7]),
                                     self._hex_string(hex_CE0[3]),
                                     self._hex_string(hex_CE0[1]),
                                     self._hex_string(hex_CE0[6]),
                                     result)




class ProtoError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


@unique
class ProtoFieldType(IntEnum):
    VARINT = 0
    INT64 = 1
    STRING = 2
    GROUPSTART = 3
    GROUPEND = 4
    INT32 = 5
    ERROR1 = 6
    ERROR2 = 7


class ByteBuf:
    def __init__(self, data, size=None):
        if data:
            self.mem = data
        
        if size is not None:
            self.data_size = size
        elif data is not None:
            self.data_size = len(data)
        else:
            raise ValueError("Either size or data must be provided")

        self.pos = 0

    def data(self):
        return self.mem

    def size(self):
        return self.data_size

    def remove_padding(self):
        padding_size = pkcs7_padding_data_length(self.mem, self.data_size, 16)
        if padding_size == 0:
            return self.data_size
        self.data_size = padding_size
        dst = (ctypes.c_uint8 * self.data_size)()
        dst = self.mem[:self.data_size]
        self.mem = dst
        return self.mem
        
        
class ProtoField:
    def __init__(self, idx, type, val):
        self.idx = idx
        self.type = type
        self.val = val

    def isAsciiStr(self):
        if (type(self.val) != bytes):
            return False

        for b in self.val:
            if b < 0x20 or b > 0x7e:
                return False
        return True

    def __str__(self):
        if ((self.type == ProtoFieldType.INT32) or
            (self.type == ProtoFieldType.INT64) or
                (self.type == ProtoFieldType.VARINT)):
            return '%d(%s): %d' % (self.idx, self.type.name, self.val)
        elif self.type == ProtoFieldType.STRING:
            if self.isAsciiStr():  # self.val.isalnum()
                return '%d(%s): "%s"' % (self.idx, self.type.name, self.val.decode('ascii'))
            else:
                return '%d(%s): h"%s"' % (self.idx, self.type.name, self.val.hex())
        elif ((self.type == ProtoFieldType.GROUPSTART) or (self.type == ProtoFieldType.GROUPEND)):
            return '%d(%s): %s' % (self.idx, self.type.name, self.val)
        else:
            return '%d(%s): %s' % (self.idx, self.type.name, self.val)


class ProtoReader:
    def __init__(self, data):
        self.data = data
        self.pos = 0

    def seek(self, pos):
        self.pos = pos

    def isRemain(self, length):
        return self.pos + length <= len(self.data)

    def read0(self):
        assert (self.isRemain(1))
        ret = self.data[self.pos]
        self.pos += 1
        return ret & 0xFF

    def read(self, length):
        assert (self.isRemain(length))
        ret = self.data[self.pos:self.pos+length]
        self.pos += length
        return ret

    def readInt32(self):
        return int.from_bytes(self.read(4), byteorder='little', signed=False)

    def readInt64(self):
        return int.from_bytes(self.read(8), byteorder='little', signed=False)

    def readVarint(self):
        vint = 0
        n = 0
        while True:
            byte = self.read0()
            vint |= ((byte & 0x7F) << (7 * n))
            if byte < 0x80:
                break
            n += 1

        return vint

    def readString(self):
        len = self.readVarint()
        return self.read(len)


class ProtoWriter:
    def __init__(self):
        self.data = bytearray()

    def write0(self, byte):
        self.data.append(byte & 0xFF)

    def write(self, bytes):
        self.data.extend(bytes)

    def writeInt32(self, int32):
        bs = int32.to_bytes(4, byteorder='little', signed=False)
        self.write(bs)

    def writeInt64(self, int64):
        bs = int64.to_bytes(8, byteorder='little', signed=False)
        self.write(bs)

    def writeVarint(self, vint):
        vint = vint & 0xFFFFFFFF
        while (vint > 0x80):
            self.write0((vint & 0x7F) | 0x80)
            vint >>= 7
        self.write0(vint & 0x7F)

    def writeString(self, bytes):
        self.writeVarint(len(bytes))
        self.write(bytes)

    def toBytes(self):
        return bytes(self.data)


class ProtoBuf:
    def __init__(self, data=None):
        self.fields = list[ProtoField]()
        if (data != None):
            if (type(data) != bytes and type(data) != dict):
                raise ProtoError(
                    'unsupport type(%s) to protobuf' % (type(data)))

            if (type(data) == bytes) and (len(data) > 0):
                self.__parseBuf(data)
            elif (type(data) == dict) and (len(data) > 0):
                self.__parseDict(data)

    def __getitem__(self, idx):
        pf = self.get(int(idx))
        if (pf == None):
            return None
        if (pf.type != ProtoFieldType.STRING):
            return pf.val
        if (type(idx) != int):
            return pf.val
        if (pf.val == None):
            return None
        if (pf.isAsciiStr()):
            return pf.val.decode('utf-8')
        return ProtoBuf(pf.val)

    def __parseBuf(self, bytes):
        reader = ProtoReader(bytes)
        while reader.isRemain(1):
            key = reader.readVarint()
            field_type = ProtoFieldType(key & 0x7)
            field_idx = key >> 3
            if (field_idx == 0):
                break
            if (field_type == ProtoFieldType.INT32):
                self.put(ProtoField(field_idx, field_type, reader.readInt32()))
            elif (field_type == ProtoFieldType.INT64):
                self.put(ProtoField(field_idx, field_type, reader.readInt64()))
            elif (field_type == ProtoFieldType.VARINT):
                self.put(ProtoField(field_idx, field_type, reader.readVarint()))
            elif (field_type == ProtoFieldType.STRING):
                self.put(ProtoField(field_idx, field_type, reader.readString()))
            else:
                raise ProtoError(
                    'parse protobuf error, unexpected field type: %s' % (field_type.name))

    def toBuf(self):
        writer = ProtoWriter()
        for field in self.fields:
            key = (field.idx << 3) | (field.type & 7)
            writer.writeVarint(key)
            if field.type == ProtoFieldType.INT32:
                writer.writeInt32(field.val)
            elif field.type == ProtoFieldType.INT64:
                writer.writeInt64(field.val)
            elif field.type == ProtoFieldType.VARINT:
                writer.writeVarint(field.val)
            elif field.type == ProtoFieldType.STRING:
                writer.writeString(field.val)
            else:
                raise ProtoError(
                    'encode to protobuf error, unexpected field type: %s' % (field.type.name))
        return writer.toBytes()

    def dump(self):
        for field in self.fields:
            print(field)

    def getList(self, idx):
        return [field for field in self.fields if field.idx == idx]

    def get(self, idx):
        for field in self.fields:
            if field.idx == idx:
                return field
        return None

    def getInt(self, idx):
        pf = self.get(idx)
        if (pf == None):
            return 0
        if ((pf.type == ProtoFieldType.INT32) or (pf.type == ProtoFieldType.INT64) or (pf.type == ProtoFieldType.VARINT)):
            return pf.val
        raise ProtoError("getInt(%d) -> %s" % (idx, pf.type))

    def getBytes(self, idx):
        pf = self.get(idx)
        if (pf == None):
            return None
        if (pf.type == ProtoFieldType.STRING):
            return pf.val
        raise ProtoError("getBytes(%d) -> %s" % (idx, pf.type))

    def getUtf8(self, idx):
        bs = self.getBytes(idx)
        if (bs == None):
            return None
        return bs.decode('utf-8')

    def getProtoBuf(self, idx):
        bs = self.getBytes(idx)
        if (bs == None):
            return None
        return ProtoBuf(bs)

    def put(self, field: ProtoField):
        self.fields.append(field)

    def putInt32(self, idx, int32):
        self.put(ProtoField(idx, ProtoFieldType.INT32, int32))

    def putInt64(self, idx, int64):
        self.put(ProtoField(idx, ProtoFieldType.INT64, int64))

    def putVarint(self, idx, vint):
        self.put(ProtoField(idx, ProtoFieldType.VARINT, vint))

    def putBytes(self, idx, data):
        self.put(ProtoField(idx, ProtoFieldType.STRING, data))

    def putUtf8(self, idx, data):
        self.put(ProtoField(idx, ProtoFieldType.STRING, data.encode('utf-8')))

    def putProtoBuf(self, idx, data):
        self.put(ProtoField(idx, ProtoFieldType.STRING, data.toBuf()))

    def __parseDict(self, data):
        for k, v in data.items():
            if (isinstance(v, int)):
                self.putVarint(k, v)
            elif (isinstance(v, str)):
                self.putUtf8(k, v)
            elif (isinstance(v, bytes)):
                self.putBytes(k, v)
            elif (isinstance(v, dict)):
                self.putProtoBuf(k, ProtoBuf(v))
            else:
                raise ProtoError('unsupport type(%s) to protobuf' % (type(v)))

    def toDict(self, out):
        for k, v in out.items():
            if (isinstance(v, int)):
                out[k] = self.getInt(k)
            elif (isinstance(v, str)):
                out[k] = self.getUtf8(k)
            elif (isinstance(v, bytes)):
                out[k] = self.getBytes(k)
            elif (isinstance(v, dict)):
                out[k] = self.getProtoBuf(k).toDict(v)
            else:
                raise ProtoError('unsupport type(%s) to protobuf' % (type(v)))
        return out

class SM3:
    def __init__(self) -> None:
        self.IV = [1937774191, 1226093241, 388252375, 3666478592, 2842636476, 372324522, 3817729613, 2969243214]
        self.TJ = [2043430169, 2043430169, 2043430169, 2043430169, 2043430169, 2043430169, 2043430169, 2043430169, 2043430169, 2043430169, 2043430169, 2043430169, 2043430169, 2043430169, 2043430169, 2043430169, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042, 2055708042]
    
    def __rotate_left(self, a: int, k: int) -> int:
        k = k % 32

        return ((a << k) & 0xFFFFFFFF) | ((a & 0xFFFFFFFF) >> (32 - k))

    def __FFJ(self, X: int, Y: int, Z: int, j: int) -> int:

        if 0 <= j and j < 16:
            ret = X ^ Y ^ Z
        elif 16 <= j and j < 64:
            ret = (X & Y) | (X & Z) | (Y & Z)

        return ret

    def __GGJ(self, X: int, Y: int, Z: int, j: int) -> int:

        if 0 <= j and j < 16:
            ret = X ^ Y ^ Z
        elif 16 <= j and j < 64:
            ret = (X & Y) | ((~X) & Z)

        return ret

    def __P_0(self, X: int) -> int:
        return X ^ (self.__rotate_left(X, 9)) ^ (self.__rotate_left(X, 17))

    def __P_1(self, X: int) -> int:
        Z = X ^ (self.__rotate_left(X, 15)) ^ (self.__rotate_left(X, 23))

        return Z

    def __CF(self, V_i: list, B_i: bytearray) -> list:

        W = []
        for i in range(16):
            weight = 0x1000000
            data = 0
            for k in range(i * 4, (i + 1) * 4):
                data = data + B_i[k] * weight
                weight = int(weight / 0x100)
            W.append(data)

        for j in range(16, 68):
            W.append(0)
            W[j] = (
                self.__P_1(W[j - 16] ^ W[j - 9] ^ (self.__rotate_left(W[j - 3], 15)))
                ^ (self.__rotate_left(W[j - 13], 7))
                ^ W[j - 6]
            )

        W_1 = []
        for j in range(0, 64):
            W_1.append(0)
            W_1[j] = W[j] ^ W[j + 4]

        A, B, C, D, E, F, G, H = V_i

        for j in range(0, 64):

            SS1 = self.__rotate_left(
                ((self.__rotate_left(A, 12)) + E + (self.__rotate_left(self.TJ[j], j)))
                & 0xFFFFFFFF,
                7,
            )

            SS2 = SS1 ^ (self.__rotate_left(A, 12))
            TT1 = (self.__FFJ(A, B, C, j) + D + SS2 + W_1[j]) & 0xFFFFFFFF
            TT2 = (self.__GGJ(E, F, G, j) + H + SS1 + W[j]) & 0xFFFFFFFF
            D = C
            C = self.__rotate_left(B, 9)
            B = A
            A = TT1
            H = G
            G = self.__rotate_left(F, 19)
            F = E
            E = self.__P_0(TT2)

        return [
            A & 0xFFFFFFFF ^ V_i[0],
            B & 0xFFFFFFFF ^ V_i[1],
            C & 0xFFFFFFFF ^ V_i[2],
            D & 0xFFFFFFFF ^ V_i[3],
            E & 0xFFFFFFFF ^ V_i[4],
            F & 0xFFFFFFFF ^ V_i[5],
            G & 0xFFFFFFFF ^ V_i[6],
            H & 0xFFFFFFFF ^ V_i[7],
        ]

    def sm3_hash(self, msg: bytes) -> bytes:
        msg = bytearray(msg)
        len1 = len(msg)
        reserve1 = len1 % 64
        msg.append(0x80)
        reserve1 = reserve1 + 1
        # 56-64, add 64 byte
        range_end = 56
        if reserve1 > range_end:
            range_end += 64

        for i in range(reserve1, range_end):
            msg.append(0x00)

        bit_length = (len1) * 8
        bit_length_str = [bit_length % 0x100]
        for i in range(7):
            bit_length = int(bit_length / 0x100)
            bit_length_str.append(bit_length % 0x100)
        for i in range(8):
            msg.append(bit_length_str[7 - i])

        group_count = round(len(msg) / 64)

        B = []
        for i in range(0, group_count):
            B.append(msg[i * 64 : (i + 1) * 64])

        V = []
        V.append(self.IV)
        for i in range(0, group_count):
            V.append(self.__CF(V[i], B[i]))

        y = V[i + 1]
        res = b""

        for i in y:
            res += int(i).to_bytes(4, "big")

        return res
        
def get_bit(val, pos):
    return 1 if val & (1 << pos) else 0

def rotate_left(v, n):
    r = (v << n) | (v >> (64 - n))
    return r & 0xffffffffffffffff

def rotate_right(v, n):
    r = (v << (64 - n)) | (v >> n) 
    return r & 0xffffffffffffffff

def key_expansion(key):
    tmp = 0
    for i in range(4, 72):
        tmp = rotate_right(key[i-1], 3)
        tmp = tmp ^ key[i-3]
        tmp = tmp ^ rotate_right(tmp, 1)
        key[i] = c_ulonglong(~key[i-4]).value ^ tmp ^ get_bit(0x3DC94C3A046D678B, (i - 4) % 62) ^ 3
    return key

def simon_dec(ct, k, c=0):
    tmp = 0
    f = 0
    key = [0] * 72

    key[0] = k[0]
    key[1] = k[1]
    key[2] = k[2]
    key[3] = k[3]

    key = key_expansion(key)

    x_i = ct[0]
    x_i1 = ct[1]

    for i in range(72-1, -1, -1):
        tmp = x_i
        f = rotate_left(x_i, 1) if c == 1 else rotate_left(x_i, 1) & rotate_left(x_i, 8)
        x_i = x_i1 ^ f ^ rotate_left(x_i, 2) ^ key[i]
        x_i1 = tmp

    pt = [x_i, x_i1]
    return pt

def simon_enc(pt, k, c=0):
    tmp = 0
    f = 0
    key = [0] * 72
    key[0] = k[0]
    key[1] = k[1]
    key[2] = k[2]
    key[3] = k[3]

    key = key_expansion(key)

    x_i = pt[0]
    x_i1 = pt[1]

    for i in range(72):
        tmp = x_i1
        f = rotate_left(x_i1, 1) if c == 1 else rotate_left(x_i1, 1) & rotate_left(x_i1, 8)
        x_i1 = x_i ^ f ^ rotate_left(x_i1, 2) ^ key[i]
        x_i = tmp

    ct = [x_i, x_i1]
    return ct
    
    

class Argus:
    def encrypt_enc_pb(data, l):
        data = list(data)
        xor_array = data[:8]

        for i in range(8, l):
            data[i] ^= xor_array[i % 8]

        return bytes(data[::-1])

    @staticmethod
    def get_bodyhash(stub: str or None = None) -> bytes:
        return (
            SM3().sm3_hash(bytes(16))[0:6]
            if stub == None or len(stub) == 0
            else SM3().sm3_hash(bytes.fromhex(stub))[0:6]
        )

    @staticmethod
    def get_queryhash(query: str) -> bytes:
        return (
            SM3().sm3_hash(bytes(16))[0:6]
            if query == None or len(query) == 0
            else SM3().sm3_hash(query.encode())[0:6]
        )

    @staticmethod
    def encrypt(xargus_bean: dict):
        protobuf = pad(bytes.fromhex(ProtoBuf(xargus_bean).toBuf().hex()), block_size)
        new_len = len(protobuf)
        sign_key = b"\xac\x1a\xda\xae\x95\xa7\xaf\x94\xa5\x11J\xb3\xb3\xa9}\xd8\x00P\xaa\n91L@R\x8c\xae\xc9RV\xc2\x8c"
        sm3_output = b"\xfcx\xe0\xa9ez\x0ct\x8c\xe5\x15Y\x90<\xcf\x03Q\x0eQ\xd3\xcf\xf22\xd7\x13C\xe8\x8a2\x1cS\x04"  # sm3_hash(sign_key + b'\xf2\x81ao' + sign_key)

        key = sm3_output[:32]
        key_list = []
        enc_pb = bytearray(new_len)

        for _ in range(2):
            key_list = key_list + list(unpack("<QQ", key[_ * 16 : _ * 16 + 16]))

        for _ in range(int(new_len / 16)):
            pt = list(unpack("<QQ", protobuf[_ * 16 : _ * 16 + 16]))
            ct = simon_enc(pt, key_list)
            enc_pb[_ * 16 : _ * 16 + 8] = ct[0].to_bytes(8, byteorder="little")
            enc_pb[_ * 16 + 8 : _ * 16 + 16] = ct[1].to_bytes(8, byteorder="little")

        b_buffer = Argus.encrypt_enc_pb(
            (b"\xf2\xf7\xfc\xff\xf2\xf7\xfc\xff" + enc_pb), new_len + 8
        )
        b_buffer = b"\xa6n\xad\x9fw\x01\xd0\x0c\x18" + b_buffer + b"ao"

        cipher = new(md5(sign_key[:16]).digest(), MODE_CBC, md5(sign_key[16:]).digest())

        return b64encode(
            b"\xf2\x81" + cipher.encrypt(pad(b_buffer, block_size))
        ).decode()

    @staticmethod
    def get_sign(
        queryhash: None or str = None,
        data: None or str = None,
        timestamp: int = int(time.time()),
        aid: int = 1233,
        license_id: int = 1611921764,
        platform: int = 0,
        sec_device_id: str = "",
        sdk_version: str = "v04.04.05-ov-android",
        sdk_version_int: int = 134744640,
    ) -> dict:
        params_dict = parse_qs(queryhash)

        return Argus.encrypt(
            {
                1: 0x20200929 << 1,  # magic
                2: 2,  # version
                3: randint(0, 0x7FFFFFFF),  # rand
                4: str(aid),  # msAppID
                5: params_dict["device_id"][0],  # deviceID
                6: str(license_id),  # licenseID
                7: params_dict["version_name"][0],  # appVersion
                8: sdk_version,  # sdkVersionStr
                9: sdk_version_int,  # sdkVersion
                10: bytes(8),  # envcode -> jailbreak Detection
                11: platform,  # platform (ios = 1)
                12: timestamp << 1,  # createTime
                13: Argus.get_bodyhash(data),  # bodyHash
                14: Argus.get_queryhash(queryhash),  # queryHash
                15: {
                    1: 1,  # signCount
                    2: 1,  # reportCount
                    3: 1,  # settingCount
                    7: 3348294860,
                },
                16: sec_device_id,  # secDeviceToken
                # 17: timestamp,                     # isAppLicense
                20: "none",  # pskVersion
                21: 738,  # callType
                23: {1: "NX551J", 2: 8196, 4: 2162219008},
                25: 2,
            }
        )

def host() -> list or []:
    hosts = [
    "api16-normal-no1a.tiktokv.eu",
    "api16-normal-c-alisg.tiktokv.com",
    "api19-normal-c-alisg.tiktokv.com",
    "api16-normal-c-useast2a.tiktokv.com",
    "api16-normal-useast5.tiktokv.us",
    "api16-core-aion-useast5.us.tiktokv.com",
    "api16-normal-aion-useast5.us.tiktokv.com",
    "api16-normal-apix-quic.tiktokv.com",
    "api16-normal-apix.tiktokv.com",
    "api16-normal-baseline.tiktokv.com",
    "api16-normal-c-useast1a.tiktokv.com",
    "api16-normal-c-useast1a.musical.ly",
    "api16-normal-quic.tiktokv.com",
    "api16-normal-useast5.us.tiktokv.com",
    "api16-normal-useast8.us.tiktokv.com",
    "api16-normal-va.tiktokv.com",
    "api16-normal-vpc2-useast5.us.tiktokv.com",
    "api16-normal-zr.tiktokv.com",
    "api16-normal.tiktokv.com",
    "api16-normal.ttapis.com",
    "api19-core-c-alisg.tiktokv.com",
    "api19-core-c-useast1a.tiktokv.com",
    "api19-core-useast5.us.tiktokv.com",
    "api19-core-va.tiktokv.com",
    "api19-core-zr.tiktokv.com",
    "api19-core.tiktokv.com",
    "api19-normal-c-useast1a.musical.ly",
    "api19-normal-c-useast1a.tiktokv.com",
    "api19-normal-useast5.us.tiktokv.com",
    "api19-normal-va.tiktokv.com",
    "api19-normal-zr.tiktokv.com",
    "api19-normal.tiktokv.com",
    "api2-19-h2.musical.ly",
    "api2.musical.ly",
    "api21-core-c-alisg.tiktokv.com",
    "api21-core-va.tiktokv.com",
    "api21-core.tiktokv.com",
    "api21-h2-eagle.tiktokv.com",
    "api21-h2.tiktokv.com",
    "api21-normal.tiktokv.com",
    "api21-va.tiktokv.com",
    "api22-core-c-alisg.tiktokv.com",
    "api22-core-c-useast1a.tiktokv.com",
    "api22-core-va.tiktokv.com",
    "api22-core-zr.tiktokv.com",
    "api22-core.tiktokv.com",
    "api22-h2-eagle.tiktokv.com",
    "api22-normal-c-alisg.tiktokv.com",
    "api22-normal-c-useast1a.tiktokv.com"
]
    return random.choice(hosts)
    

def sign(
    params: Optional[Union[dict, str]] = None,
    url: Optional[str] = None,
    data: Optional[str] = None,
    payload: Optional[Union[str, dict]] = None,
    sec_device_id: Optional[str] = None,
    cookie: Optional[Union[str, dict]] = None,
    aid: int = 1233,
    license_id: int = 1611921764,
    sdk_version_str: str = 'v05.00.06-ov-android',
    sdk_version: int = 167775296,
    platform: int = 0,
    unix: Optional[float] = None,
    version: Optional[Union[int, str]] = None,
) -> Dict[str, Any]:
    if sec_device_id is None:
        sec_device_id = "AadCFwpTyztA5j9L" + ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(9))
    if data is None and payload is not None:
        if isinstance(payload, dict):
            data = urlencode(payload)
        else:
            data = str(payload)
    elif payload is None and data is not None:
        payload = data
    if params is None and url:
        parsed = urlparse(url)
        params = dict(parse_qsl(parsed.query))
    elif params is None:
        params = {}
    if params is None:
        params = {}
    if data is None:
        data = ""
    if cookie is None:
        cookie = ""
    if unix is None:
        unix = time.time()
    else:
        unix = float(unix)
    if aid is None:
        try:
            aid = int(params.get('aid', 1233))
        except Exception:
            aid = 1233
    def _norm_to_str(v):
        if v is None:
            return ""
        if isinstance(v, dict):
            try:
                return urlencode(v)
            except Exception:
                return str(v)
        return str(v)
    payload_s = _norm_to_str(payload)
    cookie_s = _norm_to_str(cookie)
    data_s = _norm_to_str(data)
    if isinstance(params, dict):
        try:
            params_s = urlencode(params)
        except Exception:
            params_s = str(params)
    else:
        params_s = str(params)
        if "?" in params_s:
            try:
                params_s = params_s.split("?", 1)[1]
            except Exception:
                pass
    body_for_stub = data_s if data_s else payload_s
    md5_obj = hashlib.md5()
    md5_obj.update(body_for_stub.encode('utf-8'))
    x_ss_stub = md5_obj.hexdigest().upper()
    gorgon_headers = {}
    try:
        gorgon_headers = Gorgon(params_s, int(unix), payload_s, cookie_s, version).get_value()
    except Exception as e:
        gorgon_headers = {}
        gorgon_headers["_gorgon_error"] = str(e)
    try:
        x_ladon = Ladon.encrypt(int(unix), license_id, aid)
    except Exception as e:
        x_ladon = f"ERROR_LADON:{e}"
    try:
        x_argus = Argus.get_sign(
            params_s,
            x_ss_stub,
            int(unix),
            platform=platform,
            aid=aid,
            license_id=license_id,
            sec_device_id=sec_device_id,
            sdk_version=sdk_version_str,
            sdk_version_int=sdk_version
        )
    except Exception as e:
        x_argus = f"ERROR_ARGUS:{e}"
    headers = {
        **gorgon_headers,
        'x-ss-stub': x_ss_stub,
        'x-ladon': x_ladon,
        'x-argus': x_argus,
    }
    return headers

def toHexStr(num: int) -> str:
    tmp_string = hex(num & 0xFF)[2:]
    if len(tmp_string) < 2:
        tmp_string = '0' + tmp_string
    return tmp_string

def trace_id(device_id: Union[str, int] = "") -> str:
    ts_ms = int(round(time.time() * 1000))
    if device_id == "" or device_id is None:
        device_id = str(ts_ms).zfill(9)
    e = hex(ts_ms % (2 ** 32))[2:].rjust(8, '0')
    try:
        if isinstance(device_id, int):
            r_val = int(device_id)
        else:
            ds = ''.join(ch for ch in str(device_id) if ch.isalnum())
            if ds.isdigit():
                r_val = int(ds)
            else:
                md = hashlib.md5(ds.encode()).hexdigest()
                r_val = int(md[:8], 16)
    except Exception:
        r_val = ts_ms % 1000000000
    e2 = hex(r_val & 0xFFFFFFFF)[2:].rjust(8, '0')
    r = max(1, 22 - len(e2) - 4)
    seed = hex(random.getrandbits(r * 4))[2:][:r]
    c = str(len(e2)).zfill(2) + e2 + seed
    e3 = e + c
    e3_1 = e3[0:16]
    res = f"00-{e3}-{e3_1}-01"
    return res

def md5stub(body) -> str:
    if isinstance(body, (bytes, bytearray)):
        return hashlib.md5(body).hexdigest().upper()
    return hashlib.md5(str(body).encode('utf-8')).hexdigest().upper()

def xor(s: str) -> str:
    return "".join([format(ord(ch) ^ 5, '02x') for ch in s])

def Newparams(params: Optional[dict] = None) -> dict:
    if params is None:
        params = {}
    params.update({
        '_rticket': int(round(time.time() * 1000)),
        'cdid': str(uuid.uuid4()),
        'ts': int(time.time()),
        'iid': str(random.randint(1, 10**19)),
        'device_id': str(random.randint(1, 10**19)),
        'openudid': binascii.hexlify(os.urandom(8)).decode(),
    })
    return params

def xtoken(params: Optional[dict] = None, sessionid: Optional[Union[str, bytes]] = None,
           ms_token: Optional[str] = None, ts_millis: bool = False, version_suffix: str = "3.0.0") -> Dict[str, str]:
    if params and "ts" in params:
        ts = str(params["ts"])
    else:
        ts = str(int(time.time() * 1000)) if ts_millis else str(int(time.time()))
    if sessionid is None:
        key = secrets.token_bytes(32)
    elif isinstance(sessionid, bytes):
        key = sessionid
    else:
        try:
            key = bytes.fromhex(sessionid.strip())
        except Exception:
            key = str(sessionid).encode('utf-8')
    ms = ms_token if ms_token else secrets.token_hex(32)
    parts = [ms, ts]
    if params:
        device_id = params.get("device_id")
        app_version = params.get("app_version")
        if device_id:
            parts.append(str(device_id))
        if app_version:
            parts.append(str(app_version))
    payload_bytes = ("|".join(parts)).encode('utf-8') + key
    sig = hmac.new(key, payload_bytes, hashlib.sha256).hexdigest()
    return sig
