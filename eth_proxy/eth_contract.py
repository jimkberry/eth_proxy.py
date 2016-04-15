#
#
#
from tx_delegate import TransactionDelegate
from solc_caller import SolcCaller
from types import ListType
import json
import os

# By default we'd like to import a 'config' module which implements
# setup_class_logger(). Otherwise use this instead
try:
    import config
except ImportError:
    import logging
    class config(object):
        @staticmethod
        def setup_class_logger(cls_inst):
            log =  logging.getLogger(cls_inst.__class__.__name__)
            log.setLevel(logging.INFO)
            return log     

DEFAULT_META_GAS = 100001
DEFAULT_META_CREATION_GAS = 500001

class EthContract(TransactionDelegate):
    '''
    This is a class that encapsulates the data (code and metadata)
    that makes up an ethereum contract.
    
    IMPORTANT: in the function signatures there can be no spaces in the argument list!
    '''

    CREATION_CONTEXT = 'contract_creation'  # delegate context for creation tx


    def __init__(self, contract_desc_path, eth_proxy):
        '''
        The contract descriptor is a json file which acts as an
        adjunct to a contract source file
        '''
        self.log = config.setup_class_logger(self)         
        self._eth = eth_proxy
        self._folder = None
        self._methods = None
        self._hex_bytedata = None
        self._creation_tx = None # tx hash for creation transaction - might want it
        self._addr = None  # Note that the contract will have an address even if the install failed
        self._installed = False # but this will be false
        self._data = None
                
        if contract_desc_path:
            self._folder = os.path.dirname(contract_desc_path)
            self._load_metadata(contract_desc_path)
    
    def _load_metadata(self, contract_desc_path, new_data=None):
        '''
        If new_data is specified then it overwrites what is already there
        '''
        if new_data:
            self._data = new_data
        else:
            with open(contract_desc_path) as f:
                self._data = json.load(f)
        
        if self._data.get('code_filename'):
            self._codePath = os.path.join(self._folder, self._data['code_filename'])
            with open(self._codePath) as f:
                self._source_code = f.read()
            
        self._methods = self._data.get('methods')
        self._hex_bytedata = self._data.get('hex_bytedata')
    

    def generate_metadata(self, print_results=True):
        '''
        This is really for development only. It compiles the solc source code and
        creates the json metadata for eth_contract. Since it cannot know (or even guess at
        very well) gas price it instead preserves what was already there in the previous
        metadata (if any) or adds a default value that you will have to fix yourself 
        
        To use it, create at json file with at least 
        { "code_filename": "etherpoker.sol" }, instantiate the contract, 
        and then call this method
        
        OR - this can also be used for more ad-hoc testing/development. If you
        create the contract with "None" for the description path, and then call
        "new_source()" this will get called (with default gas amounts, of course)
        and can be used immediately
        '''
            
        src_data = SolcCaller.generate_metadata(self._source_code)
        if src_data == None:
            self.log.warning("Unable to generate metadata. Solc failed/not found.")
        else:
            contractName = src_data['contract_name']
            binData = src_data['bin']
            abi = src_data['abi']
            
            new_data = {}
            new_data['code_filename'] = self._data.get('code_filename') if self._data else None     
            new_data['hex_bytedata'] = binData
            new_data['methods'] = {}
            
            for meth in abi:
                gas = DEFAULT_META_GAS
                if meth['type'] == 'function':
                    key = meth['name']
                    signame = key
                elif meth['type'] == 'constructor':
                    key = 'ctor'
                    signame = contractName
                    gas = DEFAULT_META_CREATION_GAS 
                    
                old_def = {}
                if self._methods:
                    old_def = self._methods.get(key) or {}
                    
                mdata = {}
                argTypes = [inp['type'] for inp in meth['inputs']]
                mdata['sig'] = '{0}({1})'.format(signame, ','.join(argTypes))
                mdata['returns'] = [o['type'] for o in meth['outputs']] if meth.get('outputs') else []
                mdata['gas'] = old_def.get('gas') or gas 
                
                new_data['methods'][key] = mdata
            
            # print the data to the console so it can be save to file
            # TODO: Would it even be a good idea to actually write the file?
            self.log.info(json.dumps(new_data, indent=4))
            self._load_metadata(None, new_data)
      
    def new_source(self, source_code):
        '''
        Compile new source code and recreate all metadata (does not overlay over
        previous data)
        '''
        self._source_code = source_code
        self.generate_metadata()
      
#      
        
    def _methodSig(self, methodName):
        sig = None
        mData = self._methods.get(methodName)
        if mData:
            sig = mData.get('sig')
        return sig 
    
    #
    # TransactionDelegate API
    #           
    def tx_submitted(self, delegate_data, tx_hash, err_code, err_msg):
        '''
        Called after signing and submission - but before the tx shows 
        up in the chain
        '''
        if delegate_data == self.CREATION_CONTEXT:
            if err_code == TransactionDelegate.RESULT_SUCCESS:
                self._creation_tx = tx_hash
        
    def tx_complete(self, delegate_data, tx_hash, contract_addr, has_code,
                    gas_price, gas_used, err, err_msg):    
        '''
        Called when transaction is found in the chain - or times out
        '''
        self.log.info("Context: {0}, addr: {1} err: {2} - {3}".format(delegate_data, contract_addr, err, err_msg)) 
        if delegate_data == self.CREATION_CONTEXT:
            if err == TransactionDelegate.RESULT_SUCCESS:
                self._addr = contract_addr
                self._installed = has_code
            if not self._addr:
                self.log.warning(err_msg or 'Contract creation failed. No address')                
            if not self._installed:
                self.log.warning(err_msg or 'Contract creation failed. No code')          
#
# API
#
                    
    def install(self, ctor_params=None, delegate_info=None, timeout_secs=None):
        '''
        Compile the source code and install the contract.
        Returns Nothing
        Sends a submission message back to the delegate (with tx hash) when it has been signed and submitted
        Sends a creation message back to the delegate when the transaction shows up in the chain
        
        delegate_info is either a tuple (delegate_object, delegate_data) or a list of tuples for multiple delegates
 
        Caller should catch RuntimeErrrors
        '''
        
        localDelegateInfo = (self,self.CREATION_CONTEXT)
        
        # we want to install ourselves as a delegate (the first one)
        if delegate_info:
            if not type(delegate_info) == ListType: # a single tuple was passed in
                delegate_info = [localDelegateInfo, delegate_info]            
            else: # already a list - put us first
                delegate_info.insert(0, localDelegateInfo)
        else:
            raise RuntimeError("Must include a delegate")

        if self._hex_bytedata:
            byte_data = self._hex_bytedata.decode('hex')
        else:
            byte_data = SolcCaller.compile_solidity( self._source_code) 

        self._installed = False
        mData = self._methods.get('ctor')        
        self._eth.install_compiled_contract( byte_data=byte_data,
                                            ctor_sig=mData['sig'],
                                            ctor_params=ctor_params,
                                            gas=mData['gas'],
                                            delegate_info=delegate_info)        
    
    def install_sync(self, ctor_params=None, timeout_secs=None):
        '''        
        Compile the source code and install the contract, then poll synchronously for the transaction to
        be installed. When it is, return the creation message to the caller
        
        Make sure to check 
        '''
        if self._hex_bytedata:
            byte_data = self._hex_bytedata.decode('hex')        
        else:
            byte_data = SolcCaller.compile_solidity( self._source_code)         
        
        mData = self._methods.get('ctor')
        tx_data = self._eth.install_compiled_contract_sync( byte_data=byte_data, 
                                            ctor_sig=mData['sig'], 
                                            ctor_params=ctor_params,
                                            gas=mData['gas'])           
        
        self._addr = tx_data.get('contract_addr')
        self._installed = tx_data.get('has_code')        
        return tx_data
                
    def address(self):
        return self._addr
                
    def installed(self):
        return self._installed                
                
    def setAddress(self, address):
        '''
        As opposed to calling install() to (eventually) end up with an address, if you already know the address
        of a pre-existing contract, use this to set it
        '''
        self._addr = address
                
    def transaction(self, methodName, params=None, delegate_info=None, timeout_secs=None, value=0):
        '''
        Send the named transaction to the contract.
        Returns the transaction hash.
        Sends a transaction_complete message to the delegate when it is found in the blockchain
        '''
        if not self._addr:
            raise RuntimeError("Contract adddress not set.")            
      
        if not self._installed:
            raise RuntimeError("Contract not installed.")              
      
        mData = self._methods.get(methodName)        
        return self._eth.contract_function_tx(self._addr,mData['sig'], 
                                              function_parameters=params, 
                                              gas=mData['gas'],  
                                              timeout_secs=timeout_secs, 
                                              delegate_info=delegate_info,
                                              value=value)
    
     
    def transaction_sync(self, methodName, params=None, timeout_secs=None, value=0):
        '''
        Send the named transaction to the contract then poll synchronously for the result.
        Returns the transaction complete msg.
        '''        
        if not self._addr:
            raise RuntimeError("Contract adddress not set.")            
      
        if not self._installed:
            raise RuntimeError("Contract not installed.")       
      
        mData = self._methods.get(methodName)        
        return self._eth.contract_function_tx_sync(self._addr,
                                                   mData['sig'], 
                                                   function_parameters=params, 
                                                   gas=mData['gas'],  
                                                   timeout_secs=timeout_secs, 
                                                   value=value)
             
                
    def call(self, methodName, params=None):
        '''
        Issue an eth_call() to a (non-transaction) function on the local node 
        '''
        if not self._addr:
            raise RuntimeError("Contract adddress not set.")
        if not self._installed:
            raise RuntimeError("Contract not installed.")         
        mData = self._methods.get(methodName)  
        if not mData:
            raise RuntimeError("No metadata for {0}".format(methodName))
        return self._eth.contract_function_call( contract_address=self._addr,
                                                 function_signature=mData['sig'],
                                                 function_parameters=params,
                                                 result_types=mData['returns'])
              
                        
    def get_log_data(self, tx_hash, log_idx=0):
        '''
        Doesn't directly involve a contract per se, but contract methods frequently use
        logs to return data and/or error status
        TODO: Consider using topics to look up data values
        '''
        data = None
        logs = self._eth.get_transaction_logs(tx_hash)
        if logs:
            log = logs[log_idx] if len(logs) > log_idx else None
            if log:
                data = log.get('data')
        return data
        
                