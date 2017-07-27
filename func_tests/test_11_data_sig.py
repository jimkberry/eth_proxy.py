
import logging as log
import time
import json
from eth_proxy.solc_caller import SolcCaller
from eth_proxy.pyeth_client.eth_utils import sha3
from func_setups import FuncSetups


fs = FuncSetups()

# the EthProxy
eth = fs.create_proxy()

block = eth.eth_blockNumber()  # Trivial test (are we connected?)
print("\neth_blockNumber(): {0}".format(block))

keystore = fs.create_keystore()

account = fs.get_account(keystore, 0)
account2 = fs.get_account(keystore, 1)

# make some data:
#
# Keystore sign_data signs a HASH (hex string form)
#
data = {'acct': account,
        'acct2': account2,
        'two': 2 }

jdata = json.dumps(data)
data_hash =  sha3(jdata)
data_hash_str = '0x{0}'.format(data_hash.encode('hex'))


print("Sign data using account: {0}".format(account))

(sig_str, errcode, errmsg) = keystore.sign_data(account, data_hash_str)
if errcode < 0:
    print("Signing error. Code: {0}, Msg: {1}".format(errcode, errmsg))
    exit()

print("Hash: {0}".format(data_hash_str))    
print("Signature {0}".format(sig_str))

(rec_addr, errcode, errmsg) = keystore.recover_address(data_hash_str, sig_str)
if errcode < 0:
    print("Recovery error. Code: {0}, Msg: {1}".format(errcode, errmsg))
    exit()

print("Recovered addr {0}".format(rec_addr))

print('Result: {0}'.format("SUCCESS" if rec_addr == account else "FAILURE"))
