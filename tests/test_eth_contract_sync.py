import argparse
import logging as log
import pprint
import time
import os
import codecs

from eth_proxy import EthProxyHttp, TransactionDelegate, EthNodeSigner
from eth_proxy import SolcCaller, EthContract

# End-to-end test using EthContract abstraction
# in synchronous mode (for quickie development)

#defaults
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

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


eth = EthProxyHttp(rpc_host, rpc_port)

keystore = EthNodeSigner(eth)
account = keystore.list_accounts()[0]


eth.set_transaction_signer(keystore)
eth.attach_account(account)    
        
log.info("\nRunning EthContract test...\n")

ether = eth.eth_getBalance(eth.account())
log.info("Ether balance: {0}".format(ether))
    
# Create
contract = EthContract(None, eth) # No description path
contract.new_source(contract_src)
txdata = contract.install_sync([222]) # sync mode
if not contract.installed():
    raise RuntimeError("Contract creation failed")            
       
        
# Send a tx
print("Sending function TX to contract")
msg = contract.transaction_sync('SetTheInt', [863])
if msg['err']:
    raise RuntimeError("Contract TX failed: {0}".format(msg['errmsg']))    
    
# check the tx worked
print("Calling contract function")    
[result] = contract.call( 'aPublicInt')
print("Result {0}".format(result))        
    
log.info("Done EthContract test...\n")


