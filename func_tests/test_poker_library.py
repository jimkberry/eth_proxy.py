
import os
import tempfile
import logging as log
from func_setups import FuncSetups
from eth_proxy import EthProxyHttp, EthNodeSigner
from eth_proxy import EthContract
from eth_proxy.utils import bytes_to_str
import re
import os

# End-to-end test using EthContract abstraction
# in synchronous mode (for quickie development)



def insert_library_address(bytecode, libname, address):
        print bytecode
        pat = '__(.*?){0}__+'.format(libname)
        newcode = re.sub(pat,address,bytecode,0)
        print newcode
        return newcode
    
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

fs = FuncSetups()

lib_path = "./peer_mgr.sol"
     
caller_path = "./poker_table.sol"

#eth = fs.create_proxy()
eth = fs.create_proxy('https://infuranet.infura.io:443')
assert(eth)

keystore = fs.create_keystore()
assert(keystore)

account = fs.get_account(keystore, 0)

eth.set_eth_signer(keystore)
  
ether = eth.eth_getBalance(account)
log.info("Account: {0} Ether balance: {1}".format(account, ether))
if ether == 0:
    raise RuntimeError("Account has no ether.")
    
# install library
lib_con = EthContract("PeerManager",None, eth, account) # No description path
lib_con.new_source(lib_path)
txdata = lib_con.install_sync(gas=2500000) # sync mode
if not lib_con.installed():
    raise RuntimeError("library creation failed")
    
     
# create caller
call_con = EthContract("PokerTable",None, eth, account) # No description path
call_con.new_source(caller_path)
call_con.link_library('PeerManager',lib_con.address())

#bcode = call_con._hex_bytedata
#newbc = insert_library_address(bcode,'PeerManager',lib_con.address()[2:]) 
#call_con._hex_bytedata = newbc

txdata = call_con.install_sync(["Table", "foo", 1000000000, 10000000, 2, 1, 1],gas=4500000) # sync mode
if not call_con.installed():
    raise RuntimeError("Caller creation failed") 

exit() 


#
[x_val] = call_con.call('getX')     
print("X: {0}".format(x_val))

[y_val] = call_con.call('getY')     
print("y: {0}".format(y_val))

[a_val] = call_con.call('getDbA')     
print("db.a: {0}".format(a_val))
  

[b_msg] = contract.call('checkArray', [1])
msg = bytes_to_str(b_msg)       
print("struct[1] msg: {0}".format(msg))
       
[b_msg] = contract.call('checkMap', [1])
msg = bytes_to_str(b_msg)       
print("map[1] msg: {0}".format(msg))        
        
[b_msg] = contract.call('checkArray', [2])
msg = bytes_to_str(b_msg)       
print("struct[2] msg: {0}".format(msg))
        
       
[b_msg] = contract.call('checkMap', [7])
msg = bytes_to_str(b_msg)       
print("map[7] msg: {0}".format(msg))          
        
[s] = contract.call('return_string')
msg = bytes_to_str(s)       
print("return_string(): {0}".format(msg))    
        
        
        
# Send a tx
print("Sending function TX to contract")
msg = contract.transaction_sync('SetTheInt', [863])
if msg['err']:
    raise RuntimeError("Contract TX failed: {0}".format(msg['errmsg'])) 
    
rcpt = eth.eth_getTransactionReceipt(msg['tx_hash'])
print("Rcpt: {0}".format(rcpt))

logs = eth.get_transaction_logs(msg['tx_hash'])
print("Logs: {0}".format(logs))
                                         
    
# check the tx worked
print("Calling contract function")    
[result] = contract.call( 'aPublicInt')
print("Result {0}".format(result))        
    
log.info("Done EthContract test...\n")


