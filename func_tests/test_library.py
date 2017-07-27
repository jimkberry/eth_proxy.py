
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


#
# Create a simple contract with ctor params
#
lib_src = \
    '''
pragma solidity ^0.4.0;    

library TestLib
{
    struct InnerStruct {
        int32 x;
        int32 y;
    }
    
    struct DataBlock {
        int16 a;
        string str;
        int16 b;
        InnerStruct inner;
    }
    
    function TestLib()
    {
        
    }    
    
    function init(DataBlock storage db)
    {
        db.a = -1;
        db.b = -2;
        db.str = "The Data";
        db.inner.x = -100;
        db.inner.y = -200;        
    }
    
    function getInner(DataBlock storage db) internal returns(InnerStruct storage inner)
    {
        return db.inner;
    }
    
    function setA(DataBlock storage db, int16 val)  returns(int16)
    {
       db.a = val;
       return val;
    }

    function setB(DataBlock storage db, int16 val) 
    {
       db.b = val;
    }

    function setB2(DataBlock storage db, int16 val) 
    {
       db.b = val;
    }
    
    function setB3(DataBlock storage db, int16 val) 
    {
       db.b = val;
    }
    
    function setB4(DataBlock storage db, int16 val) 
    {
       db.b = val;
    }
    
    function setB5(DataBlock storage db, int16 val) 
    {
       db.b = val;
    }
    
    function setB6(DataBlock storage db, int16 val) 
    {
       db.b = val;
    }                

    function setB7(DataBlock storage db, int16 val) 
    {
       db.b = val;
    }  
    
    function setB8(DataBlock storage db, int16 val) 
    {
       db.b = val;
    }  
    
    function setB9(DataBlock storage db, int16 val) 
    {
       db.b = val;
    }  
    
    function setB10(DataBlock storage db, int16 val) 
    {
       db.b = val;
    }  
    
    function setB11(DataBlock storage db, int16 val) 
    {
       db.b = val;
    }  
    
    function setB12(DataBlock storage db, int16 val) 
    {
       db.b = val;
    }                      
}     
    '''

    
    
caller_src = \
    '''
pragma solidity ^0.4.0;   

import "{{libpath}}";
 
contract TestCaller
{

    int16 x;
    
    TestLib.DataBlock db;
    int16 y;

    function TestCaller( int16 aVal, int16 yVal)
    {
        TestLib.init(db);
        TestLib.setA(db, aVal);
        y = yVal;
        
    }

    function getX() returns (int16)
    {
        return x;
    }

    function getY() returns (int16)
    {
        return y;
    }

    function _getInner() internal returns (TestLib.InnerStruct storage)
    {
        return TestLib.getInner(db);
    }
    
    function getInnerX() returns (int32)
    {
        TestLib.InnerStruct storage i = _getInner();
        return i.x;
    }
        
    function getDbA() returns (int16)
    {
        return db.a;
    }

    function libSetA(int16 val)
    {
        TestLib.setA(db,val);                                      
        TestLib.setB(db,val); 
        TestLib.setA(db,val);                                      
        TestLib.setB2(db,val); 
        TestLib.setA(db,val);                                      
        TestLib.setB3(db,val); 
        TestLib.setA(db,val);                                      
        TestLib.setB4(db,val);
        TestLib.setA(db,val);                                      
        TestLib.setB5(db,val); 
        TestLib.setA(db,val);                                      
        TestLib.setB6(db,val); 
        TestLib.setA(db,val);                                      
        TestLib.setB7(db,val); 
        TestLib.setA(db,val);                                      
        TestLib.setB8(db,val);
        TestLib.setA(db,val);                                      
        TestLib.setB9(db,val);
        TestLib.setA(db,val);                                      
        TestLib.setB10(db,val);
               
        TestLib.setA(db,val);                                      
        TestLib.setB(db,val); 
        TestLib.setA(db,val);                                      
        TestLib.setB2(db,val); 
        TestLib.setA(db,val);                                      
        TestLib.setB3(db,val); 
        TestLib.setA(db,val);                                      
        TestLib.setB4(db,val);
        TestLib.setA(db,val);                                      
        TestLib.setB5(db,val); 
        TestLib.setA(db,val);                                      
        TestLib.setB6(db,val); 
        TestLib.setA(db,val);                                      
        TestLib.setB7(db,val); 
        TestLib.setA(db,val);                                      
        TestLib.setB8(db,val);
        TestLib.setA(db,val);                                      
        TestLib.setB9(db,val);
        TestLib.setA(db,val);                                      
        TestLib.setB10(db,val);               
     
        TestLib.setA(db,val);                                      
        TestLib.setB(db,val); 
        TestLib.setA(db,val);                                      
        TestLib.setB2(db,val); 
        TestLib.setA(db,val);                                      
        TestLib.setB3(db,val); 
        TestLib.setA(db,val);                                      
        TestLib.setB4(db,val);
        TestLib.setA(db,val);                                      
        TestLib.setB5(db,val); 
        TestLib.setA(db,val);                                      
        TestLib.setB6(db,val); 
        TestLib.setA(db,val);                                      
        TestLib.setB7(db,val); 
        TestLib.setA(db,val);                                      
        TestLib.setB8(db,val);
        TestLib.setA(db,val);                                      
        TestLib.setB9(db,val);
        TestLib.setA(db,val);                                      
        TestLib.setB10(db,val);
    }

    function libSetB(int16 val)
    {
        TestLib.setB(db,val);    
    }    

}     
    '''    
    
#

def insert_library_address(bytecode, libname, address):
        print bytecode
        pat = '__(.*?){0}__+'.format(libname)
        newcode = re.sub(pat,address,bytecode,0)
        print newcode
        return newcode
    
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

fs = FuncSetups()

lib_path = fs.write_temp_contract("test_lib.sol", lib_src)      
lib_folder = os.path.dirname(lib_path)
os.chdir(lib_folder)
lib_path = "./test_lib.sol"

# insert actual librar        print("orig_data: {0}\n".format(self._hex_bytedata)) y source
caller_src = str.replace(caller_src, '{{libpath}}', lib_path)
      
caller_path = fs.write_temp_contract("test_caller.sol", caller_src)

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
lib_con = EthContract('TestLib',None, eth, account) # No description path
lib_con.new_source(lib_path)
txdata = lib_con.install_sync() # sync mode
if not lib_con.installed():
    raise RuntimeError("library creation failed")
    
     
# create caller
call_con = EthContract("TestCaller", None, eth, account) # No description path
call_con.new_source(caller_path)

#call_con.link_library('TestLib',lib_con.address())

bcode = call_con._hex_bytedata
newbc = insert_library_address(bcode,'TestLib',lib_con.address()[2:]) 
call_con._hex_bytedata = newbc

txdata = call_con.install_sync([123, 234], gas=3000000) # sync mode
if not call_con.installed():
    raise RuntimeError("Caller creation failed") 


#
[x_val] = call_con.call('getX')     
print("X: {0}".format(x_val))

[y_val] = call_con.call('getY')     
print("y: {0}".format(y_val))

[a_val] = call_con.call('getDbA')     
print("db.a: {0}".format(a_val))

[val] = call_con.call('getInnerX')     
print("db.inner.x: {0}".format(val))
  
 
exit() 


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


