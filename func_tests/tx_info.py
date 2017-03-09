
from eth_proxy.node_signer import EthNodeSigner
from eth_proxy.solc_caller import SolcCaller
from eth_proxy.utils import hex_to_str, hex_str_to_int
from eth_proxy import EthContract
from func_setups import FuncSetups
import argparse
import os


ETH_ETHER = 10**18


parser = argparse.ArgumentParser()
parser.add_argument('tx_hash',
                    help='transaction hash',
                    type=str )
args = parser.parse_args()
tx_hash = args.tx_hash

# - - - - - - -


def print_tx_info(tx_data):    
    print("             Hash: {0}".format(tx_data['hash']))
    print("            Nonce: {0}".format(hex_str_to_int(tx_data['nonce'])))
    print("       Block Hash: {0}".format(tx_data['blockHash']))
    print("     Block Number: {0}".format(hex_str_to_int(tx_data['blockNumber'])))    
    print("Transaction Index: {0}".format(hex_str_to_int(tx_data['transactionIndex'])))
    print("             From: {0}".format(tx_data['from']))
    print("               To: {0}".format(tx_data['to']))
    print("            Value: {0}".format(hex_str_to_int(tx_data['value'])))  
    print("        Gas Price: {0}".format(hex_str_to_int(tx_data['gasPrice'])))  
    print("         Gas Sent: {0}".format(hex_str_to_int(tx_data['gas'])))
    print("       Input Data: {0}".format(tx_data['input']))
            
# - - - - - - 

fs = FuncSetups()


#eth = fs.create_proxy()
#eth = fs.create_proxy('https://propsten.infura.io:443')
#eth = fs.create_proxy('http://localhost:8545')
eth = fs.create_proxy('https://infuranet.infura.io:443')

tx_obj = eth.eth_getTransactionByHash(tx_hash)
if tx_obj is None:
    print("TX not found.")     
    exit()
    
print_tx_info(tx_obj)





exit()
        

balance = eth.eth_getBalance(table)  #
print("\nTable: {0}".format(table)) 
print("Balance: {0}".format(float(balance)/ETH_ETHER))
if not passcode:
    exit()

contract_desc = os.path.join(gamenet.__path__[0] + '/contracts/etherpoker_table_sol.json')   

tableCon = EthContract(contract_desc, eth, acct)
tableCon.setAddress(table)
# join
msg = tableCon.transaction_sync('takeAllTheEther',[passcode])
if msg['err']:
    print("TX failed: {0}".format(msg['errmsg'])) 
else:
    log_data = tableCon.get_log_data(msg['tx_hash'])
    if log_data:
        tx_msg = hex_to_str(log_data)    
        if tx_msg is not '' :
            print("Error: {0}".format(tx_msg))
        else:
            print("Success!");
            




