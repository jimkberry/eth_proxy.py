import argparse
import logging as log
import pprint
import time
import os
import codecs

from eth_proxy_http import EthProxyHttp
from eth_keystore import EthereumKeystore, AsyncKeystore
from solc_caller import SolcCaller
from tx_delegate import TransactionDelegate

#
# End-to-end test using mid-level syncronous EtherProxy API
# NOT a full unit test
# 


#defaults
keystore_path = '/home/jim/etherpoker/etherpoker/poker_keystore'

account = '0x43f41cdca2f6785642928bcd2265fe9aff02911a'
pw = 'foo'

account2 = '0x510c1ffb6d4236808e7d54bb62741681ace6ea88'

rpc_host='localhost'
#rpc_host='162.243.42.95'
rpc_port=8545


# I want logging to look like this
log.basicConfig(level=log.INFO,
                    format=('%(levelname)s:'
                                '%(name)s():'
                                '%(funcName)s():'
                                ' %(message)s'))

# don't want info logs from "requests" (there's a lot of 'em)
log.getLogger("requests").setLevel(log.WARNING)  
log.getLogger("urllib3").setLevel(log.WARNING)

# might want this
pp = pprint.PrettyPrinter(depth=6)


# Create some global test-wide objects

# the EthProxy
eth = EthProxyHttp(rpc_host, rpc_port)
block = eth.eth_blockNumber()  # Trivial test (are we connected?)
print("\neth_blockNumber(): {0}".format(block))

# A local Keystore
keystore = EthereumKeystore(keystore_path)
errmsg = keystore.unlock_account(account, pw)
if errmsg:
    print("Error unlocking acct: {0} \nMsg: {1}.".format(account, errmsg))
    exit()
print('Account unlocked.')

# Set up eth for this account
eth.set_transaction_signer(keystore)
eth.attach_account(account)

#
# Simple transaction
#
def testSimpleTx():   
    print("\nSimple Transaction")   
    
    tx_data = eth.submit_transaction_sync(to_address=account2, 
                                         data=None,
                                         gas=500001,
                                         value=123*10000)
    print("tx_hash: {0}".format(tx_data['tx_hash']))


#
# Create a simple contract with ctor params
#
contract_src = \
    '''
    contract TheTestContract 
    {
        // publics
        int32 public aPublicInt = 111;
            
        // private'ish
        address _ownerAddr;
    
        // Gas measured: ?? TODO
        function TheTestContract(int32 newInt) 
        {
            aPublicInt = newInt;
            _ownerAddr = msg.sender;
        }
        
        function SetTheInt(int32 newInt)
        {
            aPublicInt = newInt; 
        }
    }
        
    '''


def testContract():
    print("\nContract Creation")   
    byte_code = SolcCaller.compile_solidity(contract_src)
    
    tx_data = eth.install_compiled_contract_sync(byte_data=byte_code, 
                                                 ctor_sig='TheTestContract(int32)', 
                                                 ctor_params=[222],
                                                 gas=1500000)
    contract_addr = tx_data.get('contract_addr')
    print("contract addr: {0}".format(contract_addr)) 
    if not contract_addr:
        return

    print("Sending function TX to contract")
    tx_data = eth.contract_function_tx_sync( contract_addr, 'SetTheInt(int32)', 
                                             function_parameters=[863], 
                                             gas=500000)    
    
    print("tx hash: {0}".format(tx_data['tx_hash']))
    if not tx_data:
        return    
    
    print("Calling contract function")    
    result = eth.contract_function_call( contract_address=contract_addr,
                                          function_signature='aPublicInt()', 
                                          function_parameters=None,
                                          result_types=['int32'], 
                                          from_address=account)
    print("Result {0}".format(result))    
 
 
testSimpleTx()
testContract()

