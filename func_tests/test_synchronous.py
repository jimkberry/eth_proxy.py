
from eth_proxy.node_signer import EthNodeSigner
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

# Set up eth for this account
eth.set_eth_signer(keystore)

#
# Simple transaction
#
  
print("\nSimple Transaction from {0} to {1}".format(account, account2))   


tx_data = eth.submit_transaction_sync(from_address=account,
                                     to_address=account2, 
                                     data=None,
                                     gas=500001,
                                     value=123*10000)
print("tx_hash: {0}".format(tx_data['tx_hash']))


   


