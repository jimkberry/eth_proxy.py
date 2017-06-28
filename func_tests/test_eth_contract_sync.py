import logging as log
from eth_proxy import EthProxyHttp, EthNodeSigner
from eth_proxy import EthContract
from func_setups import FuncSetups

fs = FuncSetups()

# End-to-end test using EthContract abstraction
# in synchronous mode (for quickie development)


#
# Create a simple contract with ctor params
#
# contract_src = \
#     '''
#     pragma solidity ^0.4.0;     
#     contract TheTestContract 
#     {
#         // publics
#         int32 public aPublicInt = 111;
#             
#         // private'ish
#         address _ownerAddr;
#     
#         // Gas measured: ?? TODO
#         function TheTestContract(int32 newInt) 
#         {
#             aPublicInt = newInt;
#             _ownerAddr = msg.sender;
#         }
#         
#         function SetTheInt(int32 newInt)
#         {
#             aPublicInt = newInt; 
#         }
#     }     
#     '''

# For testing with no ctor params
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
        function TheTestContract() 
        {
            aPublicInt = 147;
            _ownerAddr = msg.sender;
        }
        
        function SetTheInt(int32 newInt)
        {
            aPublicInt = newInt; 
        }
    }     
    '''

contract_path = fs.write_temp_contract("test.sol", contract_src)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

#eth = fs.create_proxy()
#eth = fs.create_proxy('https://propsten.infura.io:443')
#eth = fs.create_proxy('http://localhost:8545')
eth = fs.create_proxy('https://infuranet.infura.io:443')

keystore = fs.create_keystore()
account = fs.get_account(keystore, 0)

eth.set_eth_signer(keystore)   
        
log.info("\nRunning EthContract test...\n")

ether = eth.eth_getBalance(account)
log.info("Ether balance: {0}".format(ether))
    
# Create
contract = EthContract(None, eth, account) # No description path
contract.new_source(contract_path)
#txdata = contract.install_sync([222]) # sync mode
txdata = contract.install_sync() # for no-ctor-params test
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


