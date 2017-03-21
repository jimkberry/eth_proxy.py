
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

def maybe_decode_int(hexStr):
    return hex_str_to_int(hexStr) if hexStr else "None" 

def print_tx_info(tx_data):  
    print('\nTransaction Data:')
    print('-----------------')        
    print("             Hash: {0}".format(tx_data['hash']))
    print("            Nonce: {0}".format(maybe_decode_int(tx_data['nonce'])))
    print("       Block Hash: {0}".format(tx_data['blockHash']))
    print("     Block Number: {0}".format(maybe_decode_int(tx_data['blockNumber'])))    
    print("Transaction Index: {0}".format(maybe_decode_int(tx_data['transactionIndex'])))
    print("             From: {0}".format(tx_data['from']))
    print("               To: {0}".format(tx_data['to']))
    print("            Value: {0}".format(maybe_decode_int(tx_data['value'])))  
    print("        Gas Price: {0}".format(maybe_decode_int(tx_data['gasPrice'])))  
    print("         Gas Sent: {0}".format(maybe_decode_int(tx_data['gas'])))
    print("       Input Data: {0}".format(tx_data['input']))
            
   
def print_tx_logs(logs):
    print(       "Unformatted logs: {0}".format(logs))   
            
def print_tx_receipt(rcpt):
    print("\nTransaction Receipt:")
    print('--------------------')     
    if rcpt:
        print("   Transaction Hash: {0}".format(rcpt['transactionHash']))               
        print("  Transaction Index: {0}".format(maybe_decode_int(rcpt['transactionIndex'])))
        print("         Block Hash: {0}".format(rcpt['blockHash']))
        print("      Block Nummber: {0}".format(maybe_decode_int(rcpt['blockNumber'])))                   
        print("Cumulative Gas Used: {0}".format(maybe_decode_int(rcpt['cumulativeGasUsed']))) 
        print("           Gas Used: {0}".format(maybe_decode_int(rcpt['gasUsed']))) 
        print("   Contract Address: {0}".format(rcpt['contractAddress']))  
        print_tx_logs(rcpt['logs']) 
    else:
        print("None.")
                 
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

rcpt = eth.eth_getTransactionReceipt(tx_hash)

print_tx_receipt(rcpt)

print('')

exit()
        



