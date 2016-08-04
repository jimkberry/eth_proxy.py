
from eth_proxy.node_signer import EthNodeSigner
from eth_proxy.solc_caller import SolcCaller
import func_setups as fs

# the EthProxy
eth = fs.create_proxy()

block = eth.eth_blockNumber()  # Trivial test (are we connected?)
print("\neth_blockNumber(): {0}".format(block))

keystore = fs.create_keystore(eth)

account = fs.get_account(keystore, 0)
account2 = fs.get_account(keystore, 1)

# Set up eth for this account
eth.set_eth_signer(keystore)
eth.attach_account(account)

#
# Simple transaction
#
  
print("\nSimple Transaction")   

tx_data = eth.submit_transaction_sync(to_address=account2, 
                                     data=None,
                                     gas=500001,
                                     value=123*10000)
print("tx_hash: {0}".format(tx_data['tx_hash']))


#
# Create a simple contract with ctor params
# Not using EthContract
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


print("\nContract Creation")   
byte_code = SolcCaller.compile_solidity(contract_src)

tx_data = eth.install_compiled_contract_sync(byte_data=byte_code, 
                                             ctor_sig='TheTestContract(int32)', 
                                             ctor_params=[222],
                                             gas=1500000)
contract_addr = tx_data.get('contract_addr')
print("contract addr: {0}".format(contract_addr)) 
if not contract_addr:
    raise RuntimeError("Contract creation failed")

print("Sending function TX to contract")
tx_data = eth.contract_function_tx_sync( contract_addr, 'SetTheInt(int32)', 
                                         function_parameters=[863], 
                                         gas=500000)    

print("tx hash: {0}".format(tx_data['tx_hash']))
if not tx_data:
    raise RuntimeError("Contract TX failed")   

print("Calling contract function")    
result = eth.contract_function_call( contract_address=contract_addr,
                                      function_signature='aPublicInt()', 
                                      function_parameters=None,
                                      result_types=['int32'], 
                                      from_address=account)
print("Result {0}".format(result))    


