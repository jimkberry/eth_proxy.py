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
# End-to-end test using low-level EtherProxy API
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
#ks = AsyncKeystore(keystore_path)
errmsg = keystore.unlock_account(account, pw)
if errmsg:
    print("Error unlocking acct: {0} \nMsg: {1}.".format(account, errmsg))
    exit()
print('Account unlocked.')

# A global nonce for "account"
nonce = eth.eth_getTransactionCount(account, return_raw=False)
print("nonce: {0}".format(nonce))

def wait_for_tx(tx_hash, timeout=120):
    '''
    returns (succeeded, contract_addr)  addr is none if not a contract
    '''
    addr = None
    tx_data = None 
    success = False
    now = time.time()
    end_time = now + timeout
    while now < end_time:
        log.info('Polling. {0} secs left...'.format(int(end_time - now)))
        tx_data = eth.eth_getTransactionByHash(tx_hash)
        if tx_data and tx_data['blockNumber']: #  means it's published     
            success = True    
            rcpt = eth.eth_getTransactionReceipt(tx_hash)       
            addr = rcpt.get('contractAddress')
            break
        time.sleep(4)
        now = time.time()    
    return (success, addr )


#
# Simple transaction
#
def testSimpleTx():
    global nonce    
    print("\nSimple Transaction")   
    utx = eth.prepare_transaction(to_address=account2, 
                                       from_address=account,
                                       data=None,
                                       nonce=nonce,
                                       gas=100001,
                                       value=123*10000)
    print("utx: {0}".format(utx))
    
    # we happen to know that this signer can be called synchronously
    # it's sort of a cheat. Maybe there should be an (optional?)
    # sync() API call? 
    (stx, errcode, errmsg) = keystore.sign_transaction(account, utx)
    if errcode < 0:
        print("Signing error. Code: {0}, Msg: {1}".format(errcode, errmsg))
    print("stx: {0}".format(stx))
    
    txhash = eth.eth_sendRawTransaction(stx)
    print("tx_hash: {0}".format(txhash))
    nonce += 1
    
    (success, dummy) = wait_for_tx(txhash)
    print('Found it: {0}'.format(success))

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
    global nonce
    print("\nContract Creation")   
    byte_code = SolcCaller.compile_solidity(contract_src)
    utx = eth.prepare_contract_creation_tx(byte_data=byte_code, 
                                        ctor_sig='TheTestContract(int32)', 
                                        ctor_params=[222],
                                        from_address=account,
                                        nonce=nonce,
                                        gas=1500000
                                        )    
    (stx, errcode, errmsg) = keystore.sign_transaction(account, utx)
    if errcode < 0:
        print("Signing error. Code: {0}, Msg: {1}".format(errcode, errmsg))   
    txhash = eth.eth_sendRawTransaction(stx)
    print("tx_hash: {0}".format(txhash))
    nonce += 1
    (success, contract_addr) = wait_for_tx(txhash)
    print("Contract Addr: {0}".format(contract_addr))
    if not contract_addr:
        return
    
    print("Sending function TX to contract")
    utx = eth.prepare_contract_function_tx( contract_address=contract_addr,
                                            function_signature='SetTheInt(int32)', 
                                            function_parameters=[863], 
                                            from_address=account, 
                                            nonce=nonce,
                                            gas=500000)    
    (stx, errcode, errmsg) = keystore.sign_transaction(account, utx)
    if errcode < 0:
        print("Signing error. Code: {0}, Msg: {1}".format(errcode, errmsg))   
    txhash = eth.eth_sendRawTransaction(stx)
    nonce += 1    
    print("tx_hash: {0}".format(txhash))    
    (success, dummy) = wait_for_tx(txhash)
    print("Tx found? {0}".format(success))
    if not success:
        return 
    
    print("Calling contract function")    
    result = eth.contract_function_call( contract_address=contract_addr,
                                         function_signature='aPublicInt()', 
                                         function_parameters=None,
                                         result_types=['int32'], 
                                         from_address=account)
    print("Result {0}".format(result))    
 
    
# class DummyDelegate(TransactionDelegate):
# 
#     def tx_submitted(self, delegate_data, tx_hash, err_code, err_msg):
#         print("TxHash: {0}".format(tx_hash))
#         
#     def contract_created(self, msg):
#         print("Creation msg: {0}".format(msg))
#     
#     
# def testInstallContract():
#     global nonce
#     print("\nInstallContract() test")   
#  
#     eth.attach_account(account)
#     eth.set_transaction_signer(ks)
#  
#     delg = DummyDelegate()
#  
#     eth.install_contract(contract_code=contract_src, 
#                          ctor_sig='TheTestContract(int32)', 
#                          ctor_params=[222],
#                          gas=2000000, 
#                          timeout_secs=60, 
#                          delegate_info=(delg, "test"), 
#                          byte_data=None)    
#     
#     ks.loop()
#     msg = eth.poll_until_msg()
#     print msg


testSimpleTx()
testContract()

