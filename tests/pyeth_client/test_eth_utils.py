#
#
#
from eth_proxy.pyeth_client.eth_utils import *
import rlp
import pytest

def test_to_string():
    assert to_string(27345) == '27345'
    assert to_string('foo') == 'foo'
    assert to_string(True) == 'True'

def test_int_to_bytes():
    int_to_bytes(1234567890) == 'I\x96\x02\xd2'
    
    with pytest.raises(rlp.SerializationError):
        int_to_bytes(-1) 

def test_to_string_for_regexp():
    '''
    Note that this is only different from to_string() for python3
    TODO: test python 3
    '''
    assert to_string_for_regexp(27345) == '27345'
    assert to_string_for_regexp('foo') == 'foo'
    assert to_string_for_regexp(True) == 'True'
 
def test_ceil32():
    assert ceil32(17) == 32
    assert ceil32(48) == 64
    assert ceil32(0) == 0
    assert ceil32(-63) == -32    

def test_encode_int():
    assert encode_int(123) == '{'
    assert encode_int(1234567890) == 'I\x96\x02\xd2'
    assert encode_int(0) == ''
    with pytest.raises(Exception):
        encode_int(-1)

def test_sha3():
    assert sha3(0) == \
        '\x04HR\xb2\xa6p\xad\xe5@~x\xfb(c\xc5\x1d\xe9\xfc\xb9eB\xa0q\x86\xfe:\xed\xa6\xbb\x8a\x11m'
    assert sha3('880a13d1de2ca6b4') == \
        "\xedgt\x00v\xfb\x9d\x95l-=\xac{\xb6\xc2\x99\xcf\x05\x01\x8f\xe3\xaf\xe2K\xba\xe0,'7i\xc7L"


def test_normalize_address():
    assert normalize_address('0x3c3d9b098206f68814e58b059063b915c96d54cc') == \
        '<=\x9b\t\x82\x06\xf6\x88\x14\xe5\x8b\x05\x90c\xb9\x15\xc9mT\xcc'
    assert normalize_address('3c3d9b098206f68814e58b059063b915c96d54cc') == \
        '<=\x9b\t\x82\x06\xf6\x88\x14\xe5\x8b\x05\x90c\xb9\x15\xc9mT\xcc'

def test_zpad():
    assert zpad('123', 8) == '\x00\x00\x00\x00\x00123'
    assert zpad('fobarabcdefg', 8) == 'fobarabcdefg'

def test_getSignedNumber():
    assert getSignedNumber(0x123245,64) == 1192517L
    assert getSignedNumber(0xc0123245,32) == -1072549307
    assert getSignedNumber(0xc0123245,64) == 3222417989L

    