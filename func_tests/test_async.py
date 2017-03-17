import logging as log
import time

from eth_proxy import TransactionDelegate, SolcCaller
from func_setups import FuncSetups

fs = FuncSetups()


#
# Create a simple contract with ctor params
#
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

contract_path = fs.write_temp_contract("test.sol", contract_src)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#
# Test of async calls
#


class async_tester(TransactionDelegate):
    
    # potential states
    STATE_INIT = 0 # Initialize and create the contract...
    STATE_CONTRACT_CREATED = 1 # just poll until it's installed    
    STATE_CONTRACT_INSTALLED = 2 # send a TX to the contract
    STATE_TX_SENT = 3 # poll until it's there
    STATE_TX_DONE = 4 # use a contract call() to read the result
    STATE_DONE = 7
    
    def __init__(self):
        self.state = self.STATE_INIT
        self.eth = None
        self.contract_addr = None
        self.done = False
           
        
    # 
    # TransactionDelegate API
    #
    def tx_submitted(self, delegate_data, tx_hash, err_code, err_msg):
        print("Tx_submitted callback - err: {0} Data: {1}".format(err_code, delegate_data))
        
    def tx_complete(self, delegate_data, tx_hash, contract_addr, has_code,
                    gas_price, gas_used, err, err_msg):    
        '''
        
        '''
        print("Tx complete callback - err: {0} dData: {1}".format(err, delegate_data))
        if err == TransactionDelegate.RESULT_SUCCESS:
        
            if delegate_data == 'contract_creation':
                self.contract_addr = contract_addr
                log.info("contract_addr: {0}, has_code: {1}".format(contract_addr, has_code))
                if has_code:
                    self.state = self.STATE_CONTRACT_INSTALLED 
                else:
                    self.state = self.STATE_DONE
                                 
            if delegate_data == 'test_tx':
                log.info("Contract TX in chain. Gas used: {0}".format(gas_used))
                self.state = self.STATE_TX_DONE      
        else:
            log.warning("DData: {0}, Err: {1} Msg {2}".format(delegate_data, err, err_msg)) 
            self.state = self.STATE_DONE           
   
        
    #
    #
    #
    
    def setup_ethProxy(self):
        self.eth = fs.create_proxy()
        keystore = fs.create_keystore()
        # Set up proxy for this account
        self.eth.set_eth_signer(keystore)
        #self.eth.set_dynamic_gas_price(1.1)
        self.account = fs.get_account(keystore, 0)

        
    def run(self):
        self.setup_ethProxy()
        ether = self.eth.eth_getBalance(self.account)
        log.info("Ether balance: {0}".format(ether))
        if not ether:
            return
        
        while self.state != self.STATE_DONE:
            log.info("Loop...")
            self.loop()
            time.sleep(2)        
        
    def loop(self):
        '''
        Simple finite-state looper
        state hander functions are responsible for setting new state.
        '''
        self.eth.do_poll()
                    
        if self.state == self.STATE_INIT:
            self.createContract()
        elif self.state == self.STATE_CONTRACT_CREATED:
            pass 
        elif self.state == self.STATE_CONTRACT_INSTALLED:
            self.sendContractTx()
        elif self.state == self.STATE_TX_SENT:
            pass            
        elif self.state == self.STATE_TX_DONE:
            self.checkTxResults()
        elif self.state == self.STATE_DONE:
            pass
        
        
    def createContract(self):
        print("Creating Contract...")   
        byte_code = SolcCaller.compile_solidity(contract_path)
        self.eth.install_compiled_contract( acct_address=self.account,
                                            byte_data=byte_code, 
                                            ctor_sig='TheTestContract(int32)', 
                                            ctor_params=[222],
                                            gas=1500000,
                                            delegate_info=(self,'contract_creation'))
        self.state = self.STATE_CONTRACT_CREATED     


        
    def sendContractTx(self):
        '''
        '''    
        print('Sending TX to contract...')
        self.eth.contract_function_tx( self.account, self.contract_addr, 'SetTheInt(int32)', 
                                             function_parameters=[863], 
                                             gas=50000, # uses about 27000
                                             delegate_info=(self,'test_tx'))
        self.state = self.STATE_TX_SENT         
    
 

    def checkTxResults(self):
        print("Calling contract function")    
        result = self.eth.contract_function_call( contract_address=self.contract_addr,
                                              function_signature='aPublicInt()', 
                                              function_parameters=None,
                                              result_types=['int32'], 
                                              from_address=self.account)
        print("Result {0}".format(result))    

        self.state = self.STATE_DONE        
        
           
        
#
#
#
if __name__ =="__main__":
    '''
    Test it all
    '''  
    log.info("Running async test...\n")
    tester = async_tester()
    tester.run()
    log.info("Done async test...\n")
    

