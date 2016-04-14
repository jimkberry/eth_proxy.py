#
# This module has largely been copied from pyethereum.utils
#
# In practice it turned out that importing the whole pyethereum library in order
# to access these functions made it surprisingly difficult to install client 
# applications because of pyethereum's dependencies. This is especially 
# the case on machines running OSX, and as of this writing makes it 
# impossible to install them at all under Windows.   
#

#
# From pyethereum.utils
#

import sys
import rlp
from rlp.sedes import big_endian_int, BigEndianInt, Binary
from rlp.utils import decode_hex, encode_hex, ascii_chr, str_to_bytes

from Crypto.Hash import keccak
sha3_256 = lambda x: keccak.new(digest_bits=256, data=x).digest()

big_endian_to_int = lambda x: big_endian_int.deserialize(str_to_bytes(x).lstrip(b'\x00'))
int_to_big_endian = lambda x: big_endian_int.serialize(x)

TT256 = 2 ** 256
#TT256M1 = 2 ** 256 - 1
#TT255 = 2 ** 255

if sys.version_info.major == 2:
    is_numeric = lambda x: isinstance(x, (int, long))
    is_string = lambda x: isinstance(x, (str, unicode))

    def to_string(value):
        return str(value)

    def int_to_bytes(value):
        if isinstance(value, str):
            return value
        return int_to_big_endian(value)

    def to_string_for_regexp(value):
        return str(value)


else:
    is_numeric = lambda x: isinstance(x, int)
    is_string = lambda x: isinstance(x, bytes)

    def to_string(value):
        if isinstance(value, bytes):
            return value
        if isinstance(value, str):
            return bytes(value, 'utf-8')
        if isinstance(value, int):
            return bytes(str(value), 'utf-8')

    def int_to_bytes(value):
        if isinstance(value, bytes):
            return value
        return int_to_big_endian(value)

    def to_string_for_regexp(value):
        return str(to_string(value), 'utf-8')
    
    unicode = str

isnumeric = is_numeric

def ceil32(x):
    return x if x % 32 == 0 else x + 32 - (x % 32)

def encode_int(v):
    '''encodes an integer into serialization'''
    if not is_numeric(v) or v < 0 or v >= TT256:
        raise Exception("Integer invalid or out of range: %r" % v)
    return int_to_big_endian(v)

def sha3(seed):
    return sha3_256(to_string(seed))

def normalize_address(x, allow_blank=False):
    if allow_blank and (x is None or x == ''):
        return ''
    if len(x) in (42, 50) and x[:2] == '0x':
        x = x[2:]
    if len(x) in (40, 48):
        x = decode_hex(x)
    if len(x) == 24:
        assert len(x) == 24 and sha3(x[:20])[:4] == x[-4:]
        x = x[:20]
    if len(x) != 20:
        raise Exception("Invalid address format: %r" % x)
    return x

def zpad(x, l):
    return b'\x00' * max(0, l - len(x)) + x


def getSignedNumber(number, bitLength):
    '''
    From http://stackoverflow.com/questions/28553458/how-to-create-or-interpret-custom-data-type-4bit-signed?lq=1
    '''
    mask = (2 ** bitLength) - 1
    if number & (1 << (bitLength - 1)):
        return number | ~mask
    else:
        return number & mask
