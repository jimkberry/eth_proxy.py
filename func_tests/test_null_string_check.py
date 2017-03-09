import logging as log
from eth_proxy import EthProxyHttp, EthNodeSigner
from eth_proxy import EthContract
from eth_proxy.pyeth_client.eth_utils import sha3
from eth_proxy.utils import bytes_to_str
from func_setups import FuncSetups

fs = FuncSetups()

# End-to-end test using EthContract abstraction
# in synchronous mode (for quickie development)


#
# Create a simple contract with ctor params
#
contract_src = \
    '''
    pragma solidity ^0.4.0;  
    contract TheTestContract 
    {
        // publics
        string unititializedStorageString;
        
        bytes32 constant nullStringHash = 0xc5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470;
        
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
        
        function getAddrString(address addr) constant returns(string)
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
        
        function testNullWithShaConst() constant returns(int8)
        {
            int8 ret = 0;
            if (sha3(_stringsByAddr[msg.sender])==nullStringHash)
                ret = 1;
            return ret;         
        }        
        
        
    }    
    '''

contract_path = fs.write_temp_contract("test.sol", contract_src)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# the EthProxy
#eth = fs.create_proxy()
#eth = fs.create_proxy('https://propsten.infura.io:443')
eth = fs.create_proxy('http://localhost:8545')

keystore = fs.create_keystore()
account = fs.get_account(keystore, 0)

eth.set_eth_signer(keystore)   
        
log.info("\nRunning EthContract test...\n")

ether = eth.eth_getBalance(account)
log.info("Ether balance: {0}".format(ether))
    
# Create
contract = EthContract(None, eth, account) # No description path
contract.new_source(contract_path)
txdata = contract.install_sync([]) # sync mode
if not contract.installed():
    raise RuntimeError("Contract creation failed")            
       
        
        
# Send a tx
print("Sending testNullWithLen to contract")
msg = contract.transaction_sync('testNullWithLen')
if msg['err']:
    raise RuntimeError("Contract TX failed: {0}".format(msg['errmsg']))
else:
    print(msg)  
   
# Send a tx
print("Sending testNullWithSha to contract")
msg = contract.transaction_sync('testNullWithSha')
if msg['err']:
    raise RuntimeError("Contract TX failed: {0}".format(msg['errmsg']))
else:
    print(msg)    
   
# Send a tx
print("Sending testNullWithShaConst to contract")
msg = contract.transaction_sync('testNullWithShaConst')
if msg['err']:
    raise RuntimeError("Contract TX failed: {0}".format(msg['errmsg']))
else:
    print(msg)    
   
    
log.info("Done EthContract test...\n")


