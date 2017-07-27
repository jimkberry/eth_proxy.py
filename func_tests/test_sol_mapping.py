
import logging as log
import time

from eth_proxy.solc_caller import SolcCaller
from func_setups import FuncSetups

fs = FuncSetups()

# the EthProxy
eth = fs.create_proxy()
#eth = fs.create_proxy('https://propsten.infura.io:443')
#eth = fs.create_proxy('http://localhost:8545')

block = eth.eth_blockNumber()  # Trivial test (are we connected?)
print("\neth_blockNumber(): {0}".format(block))

keystore = fs.create_keystore()

account = fs.get_account(keystore, 0)
account2 = fs.get_account(keystore, 1)

# A global nonce for "account"
nonce = eth.eth_getTransactionCount(account, return_raw=False)
print("nonce: {0}".format(nonce))

def wait_for_tx(tx_hash, timeout=300):
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
    return (success, addr, tx_data )




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
        string unititializedStorageString;
        
        mapping (address => string ) _stringsByAddr;
               
        // Gas measured: ?? TODO
        function TheTestContract() 
        {
            _stringsByAddr[msg.sender] = 'owner';
        }
        
        function addMe()
        {
            if (sha3(_stringsByAddr[msg.sender]) == sha3(""))
                _stringsByAddr[msg.sender] = 'follower';            
            
        }
        
        function getAddrString() constant returns(string)
        {
            if (sha3(_stringsByAddr[msg.sender])==sha3(""))
                return _stringsByAddr[msg.sender];
            return ""; 
        }
        
        function testNullWithLen() constant returns(int8)
        {
            int8 ret = 0;
            if (bytes(_stringsByAddr[msg.sender]).length == 0)
                ret = 1;
            return ret;         
        
        }        
        
        function testNullWithSha() constant returns(int8)
        {
            int8 ret = 0;
            if (sha3(_stringsByAddr[msg.sender])==sha3(""))
                ret = 1;
            return ret;         
        
        }
        
    }
        
    '''

contract_path = fs.write_temp_contract("test.sol", contract_src)

print("\nContract Creation")   
byte_code = SolcCaller.compile_solidity(contract_path)
utx = eth.prepare_contract_creation_tx(byte_data=byte_code, 
                                    ctor_sig='TheTestContract()', 
                                    ctor_params=[],
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
(success, contract_addr, _) = wait_for_tx(txhash)
print("Contract Addr: {0}".format(contract_addr))
if not contract_addr:
    raise RuntimeError("Contract creation failed")

print("Sending testNullWithLen TX to contract")
utx = eth.prepare_contract_function_tx( contract_address=contract_addr,
                                        function_signature='testNullWithLen()', 
                                        function_parameters=[], 
                                        from_address=account, 
                                        nonce=nonce,
                                        gas=500000)    
(stx, errcode, errmsg) = keystore.sign_transaction(account, utx)
if errcode < 0:
    print("Signing error. Code: {0}, Msg: {1}".format(errcode, errmsg))   
txhash = eth.eth_sendRawTransaction(stx)
nonce += 1    
print("tx_hash: {0}".format(txhash))    
(success, _, tx_data) = wait_for_tx(txhash)
print("Tx found? {0}".format(success))
if success:
    print("Data: {0}".format(tx_data))
else:
    raise RuntimeError("Contract TX failed") 

print("Sending testNullWithSha TX to contract")
utx = eth.prepare_contract_function_tx( contract_address=contract_addr,
                                        function_signature='testNullWithSha()', 
                                        function_parameters=[], 
                                        from_address=account, 
                                        nonce=nonce,
                                        gas=500000)    
(stx, errcode, errmsg) = keystore.sign_transaction(account, utx)
if errcode < 0:
    print("Signing error. Code: {0}, Msg: {1}".format(errcode, errmsg))   
txhash = eth.eth_sendRawTransaction(stx)
nonce += 1    
print("tx_hash: {0}".format(txhash))    
(success, _, tx_data) = wait_for_tx(txhash)
print("Tx found? {0}".format(success))
if success:
    print("Data: {0}".format(tx_data))
else:
    raise RuntimeError("Contract TX failed") 



# - -----------------



