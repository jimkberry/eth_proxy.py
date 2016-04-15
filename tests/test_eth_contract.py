import argparse
import logging as log
import pprint
import time
import os
import codecs

from eth_proxy import EthProxyHttp, TransactionDelegate, EthNodeSigner
from eth_proxy import SolcCaller, EthContract


#
# End-to-end test using high-level EthContract abstraction
# 
# *****************************************
# TODO: Umm. Except it's not. This is the same as the mid-level async test.
# I guess I copied it and never got around to writing an EthContract test 
# *****************************************
#

#defaults

rpc_host='localhost'
#rpc_host='162.243.42.95'
rpc_port=8545


# I want logging to look like this
log.basicConfig(level=log.INFO,
                    format=('%(levelname)s:'
                                '%(name)s():'
                                '%(funcName)s():'
                                ' %(message)s'))

# don't want info logs from "requests" (there's a lot of 'em)
log.getLogger("requests").setLevel(log.WARNING)  
log.getLogger("urllib3").setLevel(log.WARNING)


#
# Create a simple contract with ctor params
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

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#
# Test of async calls
#


class async_tester(object):
    
    # potential states
    STATE_INIT = 0 # Initialize and create the contract...
    STATE_CONTRACT_CREATED = 1 # just poll until it's installed    
    STATE_CONTRACT_INSTALLED = 2 # send a TX to the contract
    STATE_TX_SENT = 3 # poll until it's there
    STATE_TX_DONE = 4 # use a contract call() to read the result
    STATE_DONE = 7
    
    def __init__(self):
        self.state = self.STATE_INIT
        self.eth = None;
        self.keystore = None
        self.contract_addr = None
        self.done = False
           
        
    # 
    # TransactionDelegate API
    #
    def tx_submitted(self, delegate_data, tx_hash, err_code, err_msg):
        print("Tx_complete callback - err: {0} dData: {1}".format(err_code, delegate_data))
        
    def tx_complete(self, delegate_data, tx_hash, contract_addr, gas_price,
                    gas_used, err, err_msg):    
        '''
        
        '''
        print("err: {0} dData: {1}".format(err, delegate_data))
        if err == TransactionDelegate.RESULT_SUCCESS:
        
            if delegate_data == 'contract_creation':
                self.contract_addr = contract_addr
                log.info("contract_addr: {0}".format(contract_addr))
                if contract_addr:
                    self.state = self.STATE_CONTRACT_INSTALLED 
                else:
                    self.state = self.STATE_DONE
                                 
            if delegate_data == 'test_tx':
                log.info("Contract TX in chain")
                self.state = self.STATE_TX_DONE      
        else:
            log.warning("DData: {0}, Err: {1} Msg {2}".format(delegate_data, err, err_msg)) 
            self.state = self.STATE_DONE           
   
        
    #
    #
    #
    
    def setup_ethProxy(self):
        self.eth = EthProxyHttp(rpc_host, rpc_port)
        self.keystore = EthNodeSigner(self.eth)
        account = self.keystore.list_accounts()[0]
        # Set up proxy for this account
        self.eth.set_transaction_signer(self.keystore)
        self.eth.attach_account(account)    
        
    def run(self):
        self.setup_ethProxy()
        ether = self.eth.eth_getBalance(self.eth.account())
        log.info("Ether balance: {0}".format(ether))
        if not ether:
            return
        
        while self.state != self.STATE_DONE:
            log.info("Loop...")
            self.loop()
            time.sleep(1)        
        
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
        byte_code = SolcCaller.compile_solidity(contract_src)
        self.eth.install_compiled_contract( byte_data=byte_code, 
                                            ctor_sig='TheTestContract(int32)', 
                                            ctor_params=[222],
                                            gas=1500000,
                                            delegate_info=(self,'contract_creation'))
        self.state = self.STATE_CONTRACT_CREATED     


        
    def sendContractTx(self):
        '''
        '''    
        print('Sending TX to contract...')
        self.eth.contract_function_tx( self.contract_addr, 'SetTheInt(int32)', 
                                             function_parameters=[863], 
                                             gas=500000,
                                             delegate_info=(self,'test_tx'))
        self.state = self.STATE_TX_SENT         
    
 

    def checkTxResults(self):
        print("Calling contract function")    
        result = self.eth.contract_function_call( contract_address=self.contract_addr,
                                              function_signature='aPublicInt()', 
                                              function_parameters=None,
                                              result_types=['int32'], 
                                              from_address=self.eth.account())
        print("Result {0}".format(result))    

        self.state = self.STATE_DONE        
        
           
        
#
#
#
if __name__ =="__main__":
    '''
    Test it all
    '''
    # but I don't want info logs from "requests" (there's a lot of 'em)
    log.getLogger("requests").setLevel(log.WARNING)
    log.getLogger("urllib3").setLevel(log.WARNING)     
    
    log.info("\nRunning EthContract test...\n")
    tester = async_tester()
    tester.run()
    log.info("Done EthContract test...\n")
    

