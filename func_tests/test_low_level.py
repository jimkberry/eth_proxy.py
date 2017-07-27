
import logging as log
import time

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


# A global nonce for "account"
nonce = eth.eth_getTransactionCount(account, 'pending')
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
# Create and access a contract without
# using the EthContract class
#
contract_src = \
    '''
    pragma solidity ^0.4.0;  
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

contract_path = fs.write_temp_contract("test.sol", contract_src)

print("\nContract Creation")   
byte_code = SolcCaller.compile_solidity(contract_path, "TheTestContract")
assert(byte_code)
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
    raise RuntimeError("Contract creation failed")

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
    raise RuntimeError("Contract TX failed") 

print("Calling contract function")    
result = eth.contract_function_call( contract_address=contract_addr,
                                     function_signature='aPublicInt()', 
                                     function_parameters=None,
                                     result_types=['int32'], 
                                     from_address=account)
print("Result {0}".format(result))    
 


