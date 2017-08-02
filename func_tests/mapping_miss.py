import logging as log
from eth_proxy import EthProxyHttp, EthNodeSigner
from eth_proxy import EthContract
from func_setups import FuncSetups

fs = FuncSetups()

#
# REMEMBER: Struct mappings that miss (key doesn;t exist)
# return an instance of the struct with all fields zero-initialized
#
# weird.
#


#
# Create a simple contract with ctor params
#
contract_src = \
    '''
    pragma solidity ^0.4.0;     
    contract TheTestContract 
    {
    
       struct Player
        {   
            address addr; // player account address. 0 means empty     
            string name; //        
        }    
 
        mapping (address => Player ) _playersByAddr;        
    
        function TheTestContract() 
        {
            addPlayer(msg.sender, "Creator");
        }

        function addPlayer(address addr, string name) 
        {
            
            _playersByAddr[addr] = Player({ addr: addr,
                                            name: name });  
        }
        
        function playerName(address addr) returns(string)
        {
            Player p = _playerForAddress(addr);
            return(p.name);
        }
        
        
        function _playerForAddress(address addr) internal constant returns(Player storage)
        {
            return _playersByAddr[addr];
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
acct2 = fs.get_account(keystore, 1)
acct3 = fs.get_account(keystore, 2)

#print acct2[2:]
#if len(acct2) == 42 and acct2[:2] == '0x':
#    print('worked');
#exit()


eth.set_eth_signer(keystore)   
        
log.info("\nRunning EthContract test...\n")

ether = eth.eth_getBalance(account)
log.info("Ether balance: {0}".format(ether))
    
# Create
contract = EthContract(None, eth, account) # No description path
contract.new_source(contract_path,None) # Lazy - should specify contract name
txdata = contract.install_sync([]) # sync mode
if not contract.installed():
    raise RuntimeError("Contract creation failed")            
       

# Send a tx
print("Sending function TX to contract")
msg = contract.transaction_sync('addPlayer', [acct2,"Ralph2"])
if msg['err']:
    raise RuntimeError("Contract TX failed: {0}".format(msg['errmsg']))    
    
    
# check the tx worked
print("Calling contract function")    
[result] = contract.call( 'playerName', [acct3])
print("Result: {0}".format(result or "Not Found"))        
    
log.info("Done EthContract test...\n")


