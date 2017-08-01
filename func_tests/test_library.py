
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

lib2_src = \
    '''
pragma solidity ^0.4.0;    

library AnotherLib
{   
    struct Data{
        int x;
        int y;
    }

    function dataSum(Data storage db)  
        public
        returns(int)
    {
       return db.x + db.y;
    }
                     
}     
    '''    
    
    
caller_src = \
    '''
pragma solidity ^0.4.0;   

import "{{libpath}}";
import "{{lib2path}}";
 
contract TestCaller
{

    TestLib.DataBlock db;
    AnotherLib.Data alData;
    
    //using AnotherLib for AnotherLib.Data;
    
    int16 x;    
    int16 y;

    function TestCaller( int16 aVal, int16 yVal)
    {
        TestLib.init(db);
        TestLib.setA(db, aVal);
        y = yVal;
        
        alData.x = 123;
        alData.y = 999;
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

    function getAnotherSum()
        public
        returns (int)
    {
        return AnotherLib.dataSum(alData);
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
# Use to check EthContract.link_library()
#
def insert_library_address(bytecode, libspec, address):
    '''
    libscpe is <source_path>:<LibraryName>
    ie" ./base/contract/bob.sol:BobContract"
    '''    
    print("\n\n{0}".format(bytecode))
    pat = '__({0})__+'.format(libspec)
    newcode = re.sub(pat,address,bytecode,0)
    print("\n\n{0}".format(newcode))
    return newcode
    
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

fs = FuncSetups()

lib_path = fs.write_temp_contract("test-lib.sol", lib_src)   
lib2_path = fs.write_temp_contract("test-lib2.sol", lib2_src)   
lib_folder = os.path.dirname(lib_path)


os.chdir(lib_folder)
lib_path = "./test-lib.sol"
lib2_path = "./test-lib2.sol"

# insert actual library source path,
# needs to happen because files are written to temp
caller_src = str.replace(caller_src, '{{libpath}}', lib_path)
caller_src = str.replace(caller_src, '{{lib2path}}', lib2_path)
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
print("TestLib Address: {0}".format(lib_con.address()))

# install other library
lib2_con = EthContract('AnotherLib',None, eth, account) # No description path
lib2_con.new_source(lib2_path)
txdata = lib2_con.install_sync() # sync mode
if not lib2_con.installed():
    raise RuntimeError("library creation failed")
print("AnotherLib Address: {0}".format(lib2_con.address()))    
     
# create caller
call_con = EthContract("TestCaller", None, eth, account) # No description path
call_con.new_source(caller_path)

libs_needed = call_con.library_stubs()
print( "Libs that need to be linked: {0}".format(libs_needed))


USE_EXTERNAL_LINK = False
if USE_EXTERNAL_LINK:
    print('  >> Linking: **** Using External regex replacement ***')   
    bcode = call_con._hex_bytedata
    newbc = insert_library_address(bcode,'{0}:TestLib'.format(lib_path),lib_con.address()[2:])
    newbc2 = insert_library_address(newbc,'{0}:AnotherLib'.format(lib2_path),lib2_con.address()[2:])      
    call_con._hex_bytedata = newbc2    
else:
    print('  >> Linking: Using EthContract.link()')
    call_con.link_library('{0}:TestLib'.format(lib_path),lib_con.address())          
    call_con.link_library('{0}:AnotherLib'.format(lib2_path),lib2_con.address())
  



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


[val] = call_con.call('getAnotherSum')     
print("getAnotherSum(): {0}".format(val)) 
assert( val == 123+999)  
 
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


