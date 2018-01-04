#
#
#
from tx_delegate import TransactionDelegate
from solc_caller import SolcCaller
from types import ListType
import json
import os
import re
from eth_proxy.eth_proxy_base import EthProxyBase
from eth_proxy.utils import validate_address
from eth_proxy.pyeth_client.eth_utils import sha3, to_string
from eth_proxy.pyeth_client.eth_abi import decode_abi

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

DEFAULT_META_GAS = 200001
DEFAULT_META_CREATION_GAS = 800001

class EthContract(TransactionDelegate):
    '''
    This is a class that encapsulates the data (code and metadata)
    that makes up an ethereum contract.
    
    IMPORTANT: in the function signatures there can be no spaces in the argument list!
    '''

    CREATION_CONTEXT = 'contract_creation'  # delegate context for creation tx


    def __init__(self, contract_desc_path, eth_proxy, acct_addr):
        '''
        The contract descriptor is a json file which acts as an
        adjunct to a contract source file
        '''
        self.log = config.setup_class_logger(self)         
        self._eth = eth_proxy
        self.acct_addr = acct_addr
        self._static_gas_price = EthProxyBase.DEFAULT_GAS_PRICE  # fixed sent to eth_proxy
        self._dyn_gas_price_mul = None # if set, gas price sent is this value * the current average gas price
        self._folder = None
        self._source_path = None
        self._contract_name = None
        self._methods = None
        self._events = None        
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

        if self._data.get('contract_name'):
            self._contract_name = self._data.get('contract_name')
        
        if self._data.get('code_filename'):
            self._source_path = os.path.join(self._folder, self._data['code_filename'])
            
        self._methods = self._data.get('methods')
        self._events = self._data.get('events')
        self._hex_bytedata = self._data.get('hex_bytedata')
    
    def _make_gas_price(self):
        thePrice = self._static_gas_price #default to this
        if not thePrice:
            defPrice = self.eth_gasPrice()
            thePrice = int(float(defPrice) * self._dyn_gas_price_mul)
            if thePrice < EthProxyBase.DEFAULT_GAS_PRICE: # don;t go below or you won't get mined
                thePrice = EthProxyBase.DEFAULT_GAS_PRICE
        return thePrice

    def set_static_gas_price(self, price):
        self._static_gas_price = price
        self._dyn_gas_price_mul = None
    
    def set_dynamic_gas_price(self, multiplier):
        self._dyn_gas_price_mul = multiplier
        self._static_gas_price = None

    def generate_metadata(self, print_results=True):
        '''
        This is really for development only. It compiles the solc source code and
        creates the json metadata for eth_contract. Since it cannot know (or even guess at
        very well) gas cost it instead preserves what was already there in the previous
        metadata (if any) or adds a default value that you will have to fix yourself 
        
        To use it, create at json file with at least 
        { "code_filename": "etherpoker.sol", contract_name="contractName" }, 
        instantiate the contract, and then call this method
        
        OR - this can also be used for more ad-hoc testing/development. If you
        create the contract with "None" for the description path, and then call
        "new_source()" this will get called (with default gas amounts, of course)
        and can be used immediately
        
        TODO: This whole custom format should be replaced with the standard
        solc ABI text output (plus a dictionary of default gas amounts)
        '''
   
        src_data = SolcCaller.generate_metadata(self._source_path,self._contract_name)
        if src_data == None:
            self.log.warning("Unable to generate metadata. Solc failed/not found.")
        else:
            contractName = src_data['contract_name']
            binData = src_data['bin']
            abi = src_data['abi']
            
            new_data = {}
            new_data['contract_name'] = contractName
            new_data['code_filename'] = self._data.get('code_filename') if self._data else None     
            new_data['hex_bytedata'] = binData
            new_data['methods'] = {}
            new_data['events'] = {}
                        
            # add dummy "None" ctor
            new_data['methods']['ctor'] = {'sig': None, 'returns': None, 'gas': DEFAULT_META_CREATION_GAS  }
            
            for meth in abi:
                gas = DEFAULT_META_GAS
                if meth['type'] == 'function':
                    key = meth['name']
                    signame = key
                elif meth['type'] == 'constructor':
                    key = 'ctor'
                    signame = contractName
                    gas = DEFAULT_META_CREATION_GAS
                elif meth['type'] == 'fallback':
                    key = 'fallback'
                    signame = None
                elif meth['type'] == 'event':
                    # This would be it'as own method - except that
                    # it's sort of a hack until we start using standard ABI files
                    key = meth['name']
                    signame = None
                    edata = {}
                    argTypes = [inp['type'] for inp in meth['inputs']] 
                    event_sig= '{0}({1})'.format(key, ','.join(argTypes))
                    edata['sighash'] = '0x{0}'.format(sha3(event_sig).encode('hex'))     
                    edata['out_names']=  [inp['name'] for inp in meth['inputs'] if not inp['indexed'] ]
                    edata['out_types'] = [inp['type'] for inp in meth['inputs'] if not inp['indexed'] ]       
                    new_data['events'][key] = edata   
                                   
                if signame:
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
      
    def new_source(self, source_path, contract_name):
        '''
        Compile new source code and recreate all metadata (does not overlay over
        previous data)
        '''
        self._contract_name = contract_name
        self._source_path = source_path
        self._folder = os.path.dirname(source_path)        
        self.generate_metadata() 
        
    def library_stubs(self):
        '''
        Look in the self's bytecode for library stubs ( "__<path.contract>____")
        and return a list of them. They include both the path and the library name,
        because that's how solc does it.
        '''        
        if not self._hex_bytedata:
            raise RuntimeError("Contract has no compiled bytecode")  
        
        
        pat = '__(.*?)__+'
        matches = re.findall(pat, self._hex_bytedata)
        fullspecs = set(matches)
        return list(fullspecs)
                

    def link_library(self, librarySpec, libAddress):
        '''
        Replace library address placeholders in self's bytecode
        with the hex address of the library.
        
        The placeholder consists of 2 underscores, followed by:
        "<library source file path>:<LibraryName>", folowed by enough
        underscores to make 40 character.
        
        Yes, thou are correct, long paths, filenames or library names will completely
        much things up. As can underscores in any of those names. As of this writing 
        this code os more resiliant to underscores than solc, but you still can;t have
        double-underscores.   
        '''
        addrStr = validate_address(libAddress)
        if not addrStr:
            raise RuntimeError("Invalid library address: {0}".format(libAddress))    
        addrStr = addrStr[2:] # remove '0x' prefix
        if not self._hex_bytedata:
            raise RuntimeError("Contract has no compiled bytecode")             
            
        pat = '__{0}__+'.format(librarySpec)
        matches = re.findall(pat, self._hex_bytedata)
        if len(matches) == 0:
            raise RuntimeError("Library reference ({0}) not found".format(librarySpec))
        # print("\norig_data: {0}\n".format(self._hex_bytedata))          
        self._hex_bytedata = re.sub(pat,addrStr,self._hex_bytedata,0)            
        # print("\nout_data: {0}\n".format(self._hex_bytedata))         
               
    def link_libraries(self, libSpecs):
        '''
        Given a list of [libSpec, libAddress] pairs, do the linking.
        '''
        for spec in libSpecs:
            self.link_library(spec[0], spec[1])
            
        
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
        if err_code != TransactionDelegate.RESULT_SUCCESS:
            self.log.error('TX submission failed: {0} Hash: {1}'.format(err_msg, tx_hash))
        
        if delegate_data == self.CREATION_CONTEXT:
            if err_code == TransactionDelegate.RESULT_SUCCESS:
                self._creation_tx = tx_hash
        
    def tx_complete(self, delegate_data, tx_hash, contract_addr, has_code,
                    gas_price, gas_used, err, err_msg):    
        '''
        Called when transaction is found in the chain - or times out
        '''
        self.log.info("Context: {0}, addr: {1} HasCode: {2} err: {3} - {4}".format(delegate_data, 
                                                                                   contract_addr, 
                                                                                   has_code,
                                                                                   err, err_msg)) 
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
                    
    def install(self, ctor_params=None, delegate_info=None, timeout_secs=None, gas=None):
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
            byte_data = SolcCaller.compile_solidity( self._source_path) 

        self._installed = False
        mData = self._methods.get('ctor') 
        
        if not gas:
            gas=mData['gas']            
               
        self._eth.install_compiled_contract( self.acct_addr,
                                             byte_data=byte_data,
                                             ctor_sig=mData['sig'],
                                             ctor_params=ctor_params,
                                             gas=gas,
                                             gas_price=self._make_gas_price(),
                                             delegate_info=delegate_info)        
    
    def install_sync(self, ctor_params=None, timeout_secs=None, gas=None):
        '''        
        Compile the source code and install the contract, then poll synchronously for the transaction to
        be installed. When it is, return the creation message to the caller
        
        Make sure to check 
        '''
        if self._hex_bytedata:
            byte_data = self._hex_bytedata.decode('hex')        
        else:
            byte_data = SolcCaller.compile_solidity( self._source_path)         
        
        mData = self._methods.get('ctor')
        if not gas:
            gas=mData['gas']          
        tx_data = self._eth.install_compiled_contract_sync( self.acct_addr,
                                                             byte_data=byte_data, 
                                                             ctor_sig=mData['sig'], 
                                                             ctor_params=ctor_params,
                                                             gas=gas,
                                                             gas_price=self._make_gas_price())           
        
        self._addr = tx_data.get('contract_addr')
        self._installed = tx_data.get('has_code')        
        return tx_data
                
    def address(self):
        return self._addr
    
    def account(self):
        return self.acct_addr
                
    def installed(self):
        return self._installed                
                
    def setAddress(self, address):
        '''
        As opposed to calling install() to (eventually) end up with an address, if you already know the address
        of a pre-existing contract, use this to set it
        '''
        self._installed = False
        self._addr = address
        code = self._eth.eth_getCode(address)
        if code:
            self._installed = True
        return self._installed
                
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
        return self._eth.contract_function_tx(self.acct_addr,
                                              self._addr,
                                              mData['sig'], 
                                              function_parameters=params, 
                                              gas=mData['gas'], 
                                              gas_price=self._make_gas_price(), 
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
        return self._eth.contract_function_tx_sync(self.acct_addr,
                                                   self._addr,
                                                   mData['sig'], 
                                                   function_parameters=params, 
                                                   gas=mData['gas'],
                                                   gas_price=self._make_gas_price(),
                                                   timeout_secs=timeout_secs, 
                                                   value=value)
             
                
    def call(self, methodName, params=None, value=0):
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
        return self._eth.contract_function_call( self._addr,
                                                 mData['sig'],
                                                 function_parameters=params,
                                                 result_types=mData['returns'],
                                                 from_address=self.acct_addr,
                                                 value=value)
              
                        
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
        
        
    def get_event_data(self, tx_hash, event_name):
        '''
        Look for and fetch the data for an event with the given signature.
        A solidity Event writes a log entry with the hash of the event signature
        as one of the topics.
           
        See: https://solidity.readthedocs.io/en/develop/abi-spec.html#events
        '''
        event = self._events.get(event_name)
        assert(event)
        data = None
        logs = self._eth.get_transaction_logs(tx_hash)
        if logs:
            event_logs = [l for l in logs if len(l['topics']) and l['topics'][0]==event['sighash']]            
            if len(event_logs):              
                log_data = event_logs[0].get('data')[2:].decode('hex')
                    
                data_arr = decode_abi(event['out_types'], log_data)
                #data_arr = decode_abi(['int32'], log_data)
                # Fancy zip usage:
                data = dict(zip(event['out_names'],data_arr))
                
        return data        
                