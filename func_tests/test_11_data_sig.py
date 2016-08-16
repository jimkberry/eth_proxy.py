
import logging as log
import time
import json
from eth_proxy.solc_caller import SolcCaller
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
data = {'acct': account,
        'acct2': account2,
        'two': 2 }

jdata = json.dumps(data)

print("Sign data using account: {0}".format(account))

(hash_str, sig_str, errcode, errmsg) = keystore.sign_data(account, jdata)
if errcode < 0:
    print("Signing error. Code: {0}, Msg: {1}".format(errcode, errmsg))
    exit()

print("Hash ({0}): {1}".format(type(hash_str), hash_str))    
print("Signature {0}".format(sig_str))

(rec_addr, errcode, errmsg) = keystore.recover_address(hash_str, sig_str)
if errcode < 0:
    print("Recovery error. Code: {0}, Msg: {1}".format(errcode, errmsg))
    exit()

print("Recovered addr {0}".format(rec_addr))

print('Result: {0}'.format("SUCCESS" if rec_addr == account else "FAILURE"))
