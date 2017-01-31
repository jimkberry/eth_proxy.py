#
#
import logging
import sys
import time
from types import ListType

from tx_delegate import TransactionDelegate
from eth_signer import EthSigDelegate
from utils import hex_str_to_int
import .pyeth_client.eth_abi as abi
import .pyeth_client.eth_utils as utils
from .pyeth_client.eth_txdata import TxData

class EthProxyBase(EthSigDelegate):
    '''
    Base class for Ethereum proxy object, which implements
    a connection to an ethereum node along with other features.
    
    Like polling w/callbacks.
    
    Actually, as it turns out in the general case the caller will already have a timed
    loop running, so the proxy doesn't need to have its own thread/greenlet so much
    as it needs to expose a "loop iterator" to the caller. This is very similar to old-style 
    message-pumps (think Win32 or any one of a thousand game engines) 

    '''
    DEFAULT_GAS_FOR_TRANSACTIONS = 500000
#    DEFAULT_GAS_PRICE = 50500000000  # 50 shannon (frontier default) + 1%
    DEFAULT_GAS_PRICE = 20200000000  # 20 shannon (homestead default) + 1%
       
    # gas price sent will be the average from eth.getGasPrice() * this multiplier
    GAS_PRICE_MULT = 1.1

    # message types
    MSG_NONE = 0
    MSG_NOTHING_PENDING = 1 # called poll_until_msg but there isn;t anything to find
    MSG_TX = 2 # transaction found    
    
    
    def __init__(self):
        self.eth_signer = None # instance of an EthereumSigner
        self.log = logging.getLogger(__name__)
        self.log.setLevel(logging.INFO)        
        self.default_timeout_secs = 120        
        self._pending_tx = []   # {hash: tx_hash, timeout: timeout, 
                                #  delegate_info: (delegate, del_data) or list of em }     
        self._txs_for_sig = {}  # txs waiting for signature
        self._last_polled_block = -1 # Latest block we've polled
    
    def _call(self, method, params=None, _id=0):
        '''
        Implementation MUST define this
        '''
        raise NotImplementedError()
    
    def _nonce(self, acct_addr):
        '''
        If nonce isn't set get it from the node
        '''
        nonce = self.eth_getTransactionCount(acct_addr, 'pending')
        self.log.info("Nonce: {0} ".format(nonce))
        return nonce                                  
 
    def _makeGasPrice(self):
        defPrice = self.eth_gasPrice()
        thePrice = int(float(defPrice) * self.GAS_PRICE_MULT)
        if thePrice < self.DEFAULT_GAS_PRICE: # don;t go below or you won't get mined
            thePrice = self.DEFAULT_GAS_PRICE
        return thePrice
    
    def _get_contract_addr(self, txHash):
        '''
        Given a hash for a completed contract creation tx,
        return the contract addr
        '''
        addr = None
        rcpt = self.eth_getTransactionReceipt(txHash)
        if rcpt:           
            addr = rcpt.get('contractAddress')     
        return addr    
    
#
#  In order to check for when transactions appear in the blockchain it is necessary 
#  to poll the Ethereum node periodically. The following code implements a facility
#  allowing the code to "register" to watch for a transaction hash that interests it.
#
#  There is a general poll() API method for EthProxy which will drive the actual polling

    def _watch_for_tx(self, tx_hash, timeout_secs, gas_price=0, delegate_info=None):
        '''
        Call this to add a transaction to the list that we are interested in.
        If delegate_info is set, it points to an instance of a class which
        implements the TxDelegate mixin
        '''
        self._pending_tx.append({   'hash': tx_hash, 
                                    'timeout': timeout_secs + time.time(),
                                    'gas_price': gas_price,
                                    'delegate_info': delegate_info })                                                        
    
    def _stop_watching_for_tx(self, tx_hash):
        '''
        This does not call the delegate (in other words it doesn't implement "cancel"). 
        You probably shouldn't ever use it directly.
        TODO: There should be a separate "cancel" call if there is a call for it.
        '''        
        delPc = None
        for pc in self._pending_tx:
            if pc['hash'] == tx_hash:
                delPc = pc
                break
        if delPc:
            self._pending_tx.remove(delPc)
    
    def _poll_for_tx(self, remove_if_found):
        '''
        This is the "poller" that must be called periodically in order to drive the process.
        
        Sends info to delegate(s)

        Returns {'tx_hash' 'contract_addr', 'has_code', 'gas_used', 'gas_price', 'err': None or msg} 
          or None
        '''
        now = time.time()     
        for pc in self._pending_tx:
            # defaults
            tx_hash = pc['hash']
            contract_addr = None
            gas_price = pc['gas_price']
            gas_used = None
            err = None
            err_msg = None
            has_code = False
            
            # self.log.info('Looking for tx: {0}'.format(txHash)) # &&&                
            tx = self.eth_getTransactionByHash(str(tx_hash))
            if tx and tx['blockNumber']: # blocknumber means it's published    
                # self.log.info('Found tx: {0}'.format(tx)) # &&&       
                rcpt = self.eth_getTransactionReceipt(str(tx_hash))  # TODO: look into translating contents
                if rcpt:
                    #self.log.info('Tx rcpt: {0}'.format(rcpt)) # &&&                      
                    gas_used = int(rcpt.get('gasUsed'),16)         
                    contract_addr = rcpt.get('contractAddress')
                    if contract_addr:
                        has_code = self.eth_getCode(contract_addr) is not None
                else:
                    self.log.warning("No TX receipt for {0}".format(tx_hash))
                        
                err = TransactionDelegate.RESULT_SUCCESS
                                                                                
            elif now > pc['timeout']:       
                err = TransactionDelegate.RESULT_TIMEOUT
                err_msg = 'timeout waiting for tx'
            
            if err is not None: 
                if pc['delegate_info']:
                    delInfo = pc['delegate_info']
                    # array or single tuple?
                    if not type(delInfo) == ListType:
                        delInfo = [delInfo]
                    # notify all delegates
                    for (delg, dData) in delInfo:
                        delg.tx_complete(dData, tx_hash, contract_addr, has_code,
                                         gas_price, gas_used, err, err_msg)                       
                if remove_if_found:              
                    self._pending_tx.remove(pc)
                              
                return {'tx_hash': tx_hash,
                        'contract_addr': contract_addr, 'has_code': has_code,
                        'gas_price': gas_price, 'gas_used': gas_used, 
                        'err': err, 'err_msg': err_msg}
            
        return None
    
    def _any_tx_pending(self):
        return len(self._pending_tx) > 0
                    
#
# Utility code
#            
    def _encode_function(self, signature, param_values):
        '''
        ABI encode a contract function signature to add to a transaction
        '''
        prefix = abi.big_endian_to_int(utils.sha3(signature)[:4])

        #self.log.info("Sig: {0} Params: {1}".format(signature, param_values))

        if signature.find('(') == -1:
            raise RuntimeError('Invalid function signature. Missing "(" and/or ")"...')

        if signature.find(')') - signature.find('(') == 1:
            return abi.encode_int(prefix)

        types = signature[signature.find('(') + 1: signature.find(')')].split(',')
        encoded_params = abi.encode_abi(types, param_values)
 
        
        return abi.zpad(abi.encode_int(prefix), 4) + encoded_params

        
#
# TX Signing stuff
#
# Similar to the transaction polling, there is also a simple facility to check for 
# signed transactions returned by TransactionSigner implementations
#

    # EthSigDelegate API
    def on_transaction_signed(self, context_data, signed_tx, result_code, err_msg=None):        
        '''
        This is the callback from a TransactionSigner.
        "context_data" for this module is the "sig_id"
        '''
        self.log.info("Result code: {0} Err Msg: {1}".format(result_code, err_msg))  
        sig_id = context_data
        self.log.info("Looking for sig_id: {0}".format(sig_id))        
        self.log.info("Available job sig_ids: {0}".format(self._txs_for_sig.keys()))
        job = self._txs_for_sig.get(sig_id)
        if job: # Found it in the "waiting for it" list
            tx_hash = None
            tx_result = TransactionDelegate.RESULT_SUCCESS
            if result_code == EthSigDelegate.SUCCESS:
                # It was signed OK, so submit it
                tx_hash = self.eth_sendRawTransaction(signed_tx)
                if not tx_hash:
                    tx_result = TransactionDelegate.RESULT_FAILURE
                    err_msg = "sendRawTransaction() failed"
                else:
                    self.log.info("Submitted TX: {0}".format(tx_hash)) 
            else:
                tx_result = TransactionDelegate.RESULT_FAILURE
                err_msg = "TX signing failed. Code: {0}".format(result_code)
                
            delInfo = job.get('delegate_info') # <- this is (these are) *Transaction*Delegates
            if delInfo:
                # array or single tuple?
                if not type(delInfo) == ListType:
                    delInfo = [delInfo]
                # notify all delegates
                for (delg, dData) in delInfo:            
                    delg.tx_submitted(dData, tx_hash, tx_result, err_msg)
            else: # This is an ok thing if it as a synchronous caller
                self.log.info('Handled signing request without transaction delegate')
                                
            if tx_hash:
                # increment local nonce and start watching for tx in the blockchain
                #self._increment_nonce()
                self._watch_for_tx(tx_hash, job['timeout'], job['gas_price'], delInfo)                 
      
            del self._txs_for_sig[sig_id]
        else:
            self.log.warn("TxSigner callback with no stored requests")

    def _watch_for_sig(self, sig_id, delegate_info, timeout_secs, gas_price):
        '''
        '''
        self.log.info("Watching for sig_id: {0}".format(sig_id))       
        job = { 'sig_id': sig_id,
                'timeout': timeout_secs + time.time(),
                'gas_price': gas_price,
                'delegate_info': delegate_info }
        self._txs_for_sig[sig_id] = job
      
    def _any_sigs_pending(self):
        return len(self._txs_for_sig) > 0
                        

# - - - -  - - - -  - - - -  - - - -  - - - -  
#
# New API
# 

#
# Needed for mid- and high-level calls (not for low, node-level calls)
#
    def set_eth_signer(self, eth_signer):
        '''
        eth_signer must implement EthereumSigner and return
        data via an EthSigDelegate passed with the transaction 
        request
        '''
        self.eth_signer = eth_signer
    
#
# EthProxy mid-level async calls
#
    
    def do_poll(self, remove_if_found=True):
        '''
        In an async app this needs to be called periodically to check for incoming data.
        The return value will be None if there was nothing received.
        Otherwise, the caller should process the returned message and call again until it IS None
                               
        remove_if_found allows for non-destructive polling (multiple readers.) If you have multiple readers
        though, the last one per frame needs to have this be True. Hopefully that's self-evident. 

        '''
        msg = None
        
        cur_block = self.eth_blockNumber()
        if cur_block > self._last_polled_block:
            self.log.info("New block: {0}".format(cur_block))
            self._last_polled_block = cur_block
            msg = self._poll_for_tx(remove_if_found)
                       
        return msg
                   
    def last_polled_block(self):
        return self._last_polled_block

    def _do_submit_transaction_async(self, from_address, utx, gas_price, timeout_secs, delegate_info):
        '''
        Calls the signer which calls us back with the result. It's the 
        called-back signature delegate method which actually submits the tx 
        '''
        sig_req_id = utx[:16]
        self._watch_for_sig(sig_req_id, delegate_info, timeout_secs, gas_price)
        self.eth_signer.sign_transaction(from_address, utx, self, sig_req_id)      
 

    def submit_transaction(self, from_address=None, to_address=None, data=None,gas=None, gas_price=None, value=0, 
                              delegate_info=None, timeout_secs=None):
        '''

        '''
        timeout_secs = timeout_secs or self.default_timeout_secs  
        gas = gas or self.DEFAULT_GAS_FOR_TRANSACTIONS  
        gas_price = gas_price or self._makeGasPrice()
        
        utx = self.prepare_transaction(    to_address=to_address, 
                                           from_address=from_address,
                                           data=data,
                                           nonce=self._nonce(from_address),
                                           gas=gas,
                                           gas_price=gas_price,
                                           value=value)
        return self._do_submit_transaction_async(from_address, utx, gas_price, timeout_secs, delegate_info)        


    def install_compiled_contract(self, acct_address=None, byte_data=None, ctor_sig=None, ctor_params=None, 
                                  gas=None, gas_price=None,  value=0, 
                                  delegate_info=None, timeout_secs=None):
        '''

        ''' 
        timeout_secs = timeout_secs or self.default_timeout_secs  
        gas = gas or self.DEFAULT_GAS_FOR_TRANSACTIONS  
        gas_price = gas_price or self._makeGasPrice()
        
        utx = self.prepare_contract_creation_tx(byte_data=byte_data,
                                             ctor_sig=ctor_sig,
                                             ctor_params=ctor_params,
                                             from_address=acct_address,
                                             nonce=self._nonce(acct_address),
                                             gas=gas,                                           
                                             gas_price=gas_price,
                                             value=value )            
        
        return self._do_submit_transaction_async(acct_address, utx, gas_price, timeout_secs, delegate_info)

    def contract_function_tx(self, from_address=None, contract_address=None, function_signature=None,
                             function_parameters=None, gas=None, gas_price=None, value=0,
                              delegate_info=None, timeout_secs=None):
        """
        Submit a transaction to a contract function on the pending block 
        Function sig is the ABI function signature, in the form 'funcname(type1,type2)' with no spaces
        """
        timeout_secs = timeout_secs or self.default_timeout_secs  
        gas = gas or self.DEFAULT_GAS_FOR_TRANSACTIONS  
        gas_price = gas_price or self._makeGasPrice()
           
        utx = self.prepare_contract_function_tx(contract_address=contract_address,
                                                function_signature=function_signature, 
                                                function_parameters=function_parameters, 
                                                from_address=from_address, 
                                                nonce=self._nonce(from_address), 
                                                gas=gas, 
                                                gas_price=gas_price, 
                                                value=value)    
        return self._do_submit_transaction_async(from_address,utx, gas_price, timeout_secs, delegate_info)
               
    
#
# EthProxy mid-level synchronous calls
#
# These assume that attachAccount() and setTransactionSigner() 
# have been called and that the signer is ready to sign TXs for
# the account
#
# For the most part these are here to allow for simple serial
# scripts. Tests or "hey! Let me try something..." ideas where
# it would be a hassle to setup delegate classes and async polling 
# and that kinda stuff.
#

    def poll_until_tx(self, remove_if_found=True, loop_secs=1):
        '''
        Called by synchronous code - sleep/poll's until it either
        times out or finds a tx it's looking for in the chain
        Returns None if there's nothing to look for
        '''
        self.log.info('Starting...')
        tx_data = None       
        while self._any_tx_pending() or self._any_sigs_pending():
            self.log.info('Polling...')
            tx_data = self.do_poll(remove_if_found)
            if tx_data:
                break
            time.sleep(loop_secs)
        return tx_data 


    def _do_wait_for_tx(self):
        '''
        Wait for the next tx in the chain
        Returns a dict full of tx_info
        '''
        tx = None
        while not tx:
            tx = self.poll_until_tx(remove_if_found=True)
        return tx          
  
    def submit_transaction_sync(self,from_address=None, to_address=None, data=None,gas=None, gas_price=None, 
                                  value=0,timeout_secs=None):
        '''
        Submit async with this class as the delegate, 
        then wait for the tx in the chain
        Returns a dict full of tx_info
        '''        
        self.submit_transaction(    from_address=from_address,
                                    to_address=to_address, 
                                    data=data,
                                    gas=gas,
                                    gas_price=gas_price,
                                    value=value,
                                    timeout_secs=timeout_secs)
        
        return self._do_wait_for_tx()
  
    def install_compiled_contract_sync(self, acct_address=None, byte_data=None, ctor_sig=None, ctor_params=None, 
                                       gas=None, gas_price=None,  value=0, timeout_secs=None):
        
        self.install_compiled_contract(acct_address=acct_address, 
                                       byte_data=byte_data, 
                                       ctor_sig=ctor_sig,
                                       ctor_params=ctor_params, 
                                       gas=gas,
                                       gas_price=gas_price,
                                       value=value, 
                                       timeout_secs=timeout_secs)
        return self._do_wait_for_tx()
  
    def contract_function_tx_sync(self, from_address=None, contract_address=None, function_signature=None,
                                  function_parameters=None,
                                  gas=None, gas_price=None, value=0, delegate_info=None, timeout_secs=None):
        '''
        '''
        self.contract_function_tx(   from_address=from_address,
                                     contract_address=contract_address,
                                     function_signature=function_signature,
                                     function_parameters=function_parameters,
                                     gas=gas, 
                                     gas_price=gas_price,
                                     value=value,
                                     timeout_secs=timeout_secs)
        return self._do_wait_for_tx()

#
#
# EthProxy lowest level
# 
# TODO: still need to implement sendTransaction(), even though we don;t really use it
# 
#

    def prepare_transaction(self, to_address=None, from_address=None,
                            data=None, nonce=None, gas=None, gas_price=None, value=0):
        '''
        Builds a simple RLP-encoded transaction (suitable for signing) from parameters.
        What makes it "simple" is that the "data" parameter is just that: a single paraemter.
        If you want to create or call a contract then you will want to call a higher-level 
        method (see below)the encodes the data and then calls this
        
        Returns an unsigned tx hash. 
        '''
        # Default values for gas and gas_price
        gas = gas or self.DEFAULT_GAS_FOR_TRANSACTIONS
        gas_price = gas_price or self._makeGasPrice()
 
        self.log.info("gas: {0}, gas_price: {1}".format(gas, gas_price))
 
        # require from address
        if not from_address:
            raise(RuntimeError('No from _address specified.'))        

        # TODO: should data be optional instead?
        if data is None:
            data = ''
            
        if nonce is None:
            nonce = 0

        ethTx = TxData( nonce, gas_price, gas, to_address, value, data)
        hex_tx = ethTx.getUnsignedTxData()   
        return hex_tx
 
    def prepare_contract_creation_tx(self, byte_data=None, ctor_sig=None, ctor_params=None,
                                     from_address=None, nonce=None, gas=None, gas_price=None, value=0):
        '''
        Encodes a transaction to create/install a contract onto the blockchain.
        
        Byte data is the COMPILED code. How you get it compiled is your business,
        but the higher-level EthContract class is your friend.
        
        TODO: try doing this using the JSON-RPC calls to compile code.   
        '''     
        # constructor parameters
        if ctor_sig:
            types = ctor_sig[ctor_sig.find('(') + 1: ctor_sig.find(')')].split(',')
            encoded_params = abi.encode_abi(types, ctor_params)                
            byte_data = byte_data + encoded_params 
 
        return self.prepare_transaction(to_address=None, 
                                             from_address=from_address,
                                             data=byte_data,
                                             nonce=nonce,
                                             gas=gas, 
                                             gas_price=gas_price, 
                                             value=value)
 
 
    def prepare_contract_function_tx(self, contract_address=None, function_signature=None, function_parameters=None, 
                                     from_address=None, nonce=None, gas=None, gas_price=None, value=0):
        '''
        Encodes the data needed to call a contract function and then passes it to prepareSimpleTransaction()
        
        Function sig is the ABI function signature, in the form 'funcname(type1,type2)' with no spaces         
        '''
        data = self._encode_function(function_signature, function_parameters)
        
        return self.prepare_transaction(to_address=contract_address, 
                                             from_address=from_address,
                                             data=data,
                                             nonce=nonce,
                                             gas=gas, 
                                             gas_price=gas_price, 
                                             value=value)
        

 
 
    def contract_function_call(self, contract_address=None, function_signature=None,
                               function_parameters=None, 
                               result_types=None, from_address=None, value=0, default_block="latest"):
        """
        Call (using eth_call) a contract function on the latest block (does NOT issue a transaction)
        Function sig is the ABI function signature, in the form 'funcname(type1,type2)' with no spaces   
        """     
        data = self._encode_function(function_signature, function_parameters)
        params = [
            {
                'to': contract_address,
                'data': '0x{0}'.format(data.encode('hex')),
                'value': "0x{0:x}".format(value)
            },
            default_block
        ]
        
        # It's technically possible to call without a from address, but msg.sender
        # will not be set properly. 

        if from_address:
            params[0]['from'] = from_address
        response = self._call('eth_call', params)
        
        # TODO: I *think* that any time "response" is the string "0x" that 
        # means the call crashed/threw. In any case, I don;ttthink you can call
        # decode_abi with a non-empty types array and an empty string.
        # So should probably be catching it and doing something more sensible
        
        # response will always begine with a "0x". If there is no result (almost
        # certainly a throw or crash, since this is a call) it is JUST the string
        # '0x'
        retVal = [None]       
        if len(response) > 2:

            retVal = abi.decode_abi(result_types, response[2:].decode('hex'))
        else:
            self.log.info("Resp: {0}".format(response))
                
        return retVal
 

    def get_transaction_logs(self, tx_hash):
        '''
        Transaction logs can be used to "return" data and/or error status. 
        This simply returns the 'logs' array from the transaction receipt 
        for the give transactio hash
        '''
        logs = None
        rcpt = self.eth_getTransactionReceipt(tx_hash)
        if rcpt:           
            logs = rcpt.get('logs')  
        return logs 
 
#
#
# Ethereum node API 
#
# 
  
    def eth_sendTransaction(self, to_address=None, from_address=None,  nonce=None,
                            data=None, gas=None, gas_price=None, value=0):
        '''
        Sending account must be unlocked on ethereum node
        ''' 
        raise NotImplementedError()
 
     
    def eth_sendRawTransaction(self, raw_tx_data):
        '''
        Sending account must be unlocked on ethereum node
        ''' 
        return self._call('eth_sendRawTransaction', [raw_tx_data])
 
 
    def eth_call(self, to_address, data=None, code=None, default_block="latest"):
        """
        I've never had any need for this.
        TODO: Test this. Nothing in eth_proxy currently uses it.
        TODO: Do something with "code"?
        TODO: unpack response?
        """
        self.log.warn("This method is still in development. See the source for details.")
        
        data = data or []
        params = [
            {
                'to': to_address,
                'data': '0x{0}'.format(data.encode('hex'))
            },
            default_block
        ]
        response = self._call('eth_call', params)
        return response

    def web3_clientVersion(self):
        """
        Returns the current client version.
        """
        result = self._call('web3_clientVersion')
        return result

    def web3_sha3(self, data):
        """
        Returns SHA3 of the given data.
        """
        data = str(data).encode('hex')
        return self._call('web3_sha3', [data])

    def net_version(self):
        """
        Returns the current network protocol version.
        """
        return self._call('net_version')

    def net_listening(self):
        """
        Returns true if client is actively listening for network connections.
        """
        return self._call('net_listening')

    def net_peerCount(self):
        """
        Returns number of peers currently connected to the client.
        NEEDS_TRANSLATION
        """
        return self._call('net_peerCount')

    def eth_version(self):
        """
        Returns the current ethereum protocol version.
        """
        return self._call('eth_version')

    def eth_coinbase(self):
        """
        Returns the client coinbase address.
        """
        return self._call('eth_coinbase')

    def eth_mining(self):
        """
        Returns true if client is actively mining new blocks.
        """
        return self._call('eth_mining')

    def eth_gasPrice(self, return_raw=False):
        """
        Returns the current price per gas in wei.
        """
        result = self._call('eth_gasPrice')
        if not return_raw:
            result = hex_str_to_int(result)
        return result    

    def eth_accounts(self):
        """
        Returns a list of addresses owned by client.
        """
        return self._call('eth_accounts')

    def eth_sign(self, addr, data):
        """
        Given an account managed by the node and some data, 
        sign the data and return the result
        """
        return self._call('eth_sign', [addr, data])

    def eth_blockNumber(self, return_raw=False):
        """
        Returns the number of most recent block.
        """
        result = self._call('eth_blockNumber')
        if not return_raw:
            result = hex_str_to_int(result)
        return result
    
    def eth_getBalance(self, address, default_block="latest", return_raw=False):
        """
        Returns the balance of the account of given address.
        """
        result = self._call('eth_getBalance', [address, default_block])
        if not return_raw:
            result = hex_str_to_int(result)
        return result

    def eth_getStorageAt(self, address, position, default_block="latest"):
        """
        Returns the value from a storage position at a given address.
        """
        return self._call('eth_getStorageAt', [address, hex(position), default_block])

    def eth_getTransactionCount(self, address, default_block="latest", return_raw=False):
        """
        Returns the number of transactions send from a address.
        """
        result = self._call('eth_getTransactionCount', [address, default_block])
        if not return_raw:
            result = hex_str_to_int(result)
        return result

    def eth_getBlockTransactionCountByHash(self, block_hash):
        """
        Returns the number of transactions in a block from a block matching the given block hash.
        NEEDS_TRANSLATION
        """
        return self._call('eth_getTransactionCount', [block_hash])

    def eth_getBlockTransactionCountByNumber(self, block_number):
        """
        Returns the number of transactions in a block from a block matching the given block number.
        NEEDS_TRANSLATION
        """
        return self._call('eth_getBlockTransactionCountByNumber', [hex(block_number)])

    def eth_getUncleCountByblockHash(self, block_hash):
        """
        Returns the number of uncles in a block from a block matching the given block hash.
        NEEDS_TRANSLATION
        """
        return self._call('eth_getUncleCountByblockHash', [block_hash])

    def eth_getUncleCountByblockNumber(self, block_number):
        """
        Returns the number of uncles in a block from a block matching the given block number.
        NEEDS_TRANSLATION
        """
        return self._call('eth_getUncleCountByblockNumber', [hex(block_number)])

    def eth_getCode(self, address, default_block="latest", return_raw=False):
        """
        Returns code at a given address.
        Result is a hex string ("0x...")
        NOTE: currently if this is called for an address with no code
        the string "0x" is returned. Hopefully this method is handling it in
        a future proof way (in case they fix it) 
        
        Return the code as a hex string or None
        """
        result = self._call('eth_getCode', [address, default_block])
        if not return_raw:
            if result == '0x' or result == '' or result is None:
                result = None
        return result        
        
        
        return self._call('eth_getCode', [address, default_block])

    def eth_getBlockByHash(self, block_hash, transaction_objects=True):
        """
        Returns information about a block by hash.
        """
        return self._call('eth_getBlockByHash', [block_hash, transaction_objects])

    def eth_flush(self):
        """
        """
        return self._call('eth_flush')

    def eth_getBlockByNumber(self, block_number, transaction_objects=True):
        """
        Returns information about a block by hash.
        """
        return self._call('eth_getBlockByNumber', [block_number, transaction_objects])

    def eth_getTransactionByHash(self, transaction_hash):
        """
        Returns the information about a transaction requested by transaction hash.
        Result is a dict
        """
        return self._call('eth_getTransactionByHash', [transaction_hash])

    def eth_getTransactionByblockHashAndIndex(self, block_hash, index):
        """
        Returns information about a transaction by block hash and transaction index position.
        """
        return self._call('eth_getTransactionByblock_hashAndIndex', [block_hash, hex(index)])

    def eth_getTransactionByblockNumberAndIndex(self, block_number, index):
        """
        Returns information about a transaction by block number and transaction index position.
        """
        return self._call('eth_getTransactionByblock_numberAndIndex', [block_number, hex(index)])

    def eth_getTransactionReceipt(self, transaction_hash):
        """
        Returns the transaction receipt requested by transaction hash.
        result is a dict.
        """
        return self._call('eth_getTransactionReceipt', [transaction_hash])

    def eth_getUncleByblockHashAndIndex(self, block_hash, index, transaction_objects=True):
        """
        Returns information about a uncle of a block by hash and uncle index position.
        """
        return self._call('eth_getUncleByblock_hashAndIndex', [block_hash, hex(index), transaction_objects])

    def eth_getUncleByblockNumberAndIndex(self, block_number, index, transaction_objects=True):
        """
        Returns information about a uncle of a block by number and uncle index position.
        """
        return self._call('eth_getUncleByblock_numberAndIndex', [block_number, hex(index), transaction_objects])

    def eth_getCompilers(self):
        """
        Returns a list of available compilers in the client.
        """
        return self._call('eth_getCompilers')

    def eth_compileSolidity(self, code):
        """
        Returns compiled solidity code.
        """
        return self._call('eth_compileSolidity', [code])

    def eth_compileLLL(self, code):
        """
        Returns compiled LLL code.
        """
        return self._call('eth_compileLLL', [code])

    def eth_compileSerpent(self, code):
        """
        Returns compiled serpent code.
        """
        return self._call('eth_compileSerpent', [code])

    def eth_newFilter(self, from_block="latest", to_block="latest", address=None, topics=None):
        """
        Creates a filter object, based on filter options, to notify when the state changes (logs).
        To check if the state has changed, call eth_getFilterChanges.
        """
        _filter = {
            'fromBlock': from_block,
            'toBlock': to_block,
            'address': address,
            'topics': topics
        }
        return self._call('eth_newFilter', [_filter])

    def eth_newBlockFilter(self, default_block="latest"):
        """
        Creates a filter object, based on an option string, to notify when state changes (logs). To check if the state has changed, call eth_getFilterChanges.
        """
        return self._call('eth_newBlockFilter', [default_block])

    def eth_uninstallFilter(self, filter_id):
        """
        Uninstalls a filter with given id. Should always be called when watch is no longer needed. Additionally Filters timeout when they aren't requested with eth_getFilterChanges for a period of time.
        """
        return self._call('eth_uninstallFilter', [filter_id])

    def eth_getFilterChanges(self, filter_id):
        """
        Polling method for a filter, which returns an array of logs which occurred since last poll.
        """
        return self._call('eth_getFilterChanges', [filter_id])

    def eth_getFilterLogs(self, filter_id):
        """
        Returns an array of all logs matching filter with given id.
        """
        return self._call('eth_getFilterLogs', [filter_id])

    def eth_getLogs(self, filter_object):
        """
        Returns an array of all logs matching a given filter object.
        """
        return self._call('eth_getLogs', [filter_object])

    def eth_getWork(self):
        """
        Returns the hash of the current block, the seedHash, and the difficulty to be met.
        """
        return self._call('eth_getWork')

    def eth_submitWork(self, nonce, header, mix_digest):
        """
        Used for submitting a proof-of-work solution.
        """
        return self._call('eth_submitWork', [nonce, header, mix_digest])

    def db_putString(self, database_name, key_name, string):
        """
        Stores a string in the local database.
        """
        return self._call('db_putString', [database_name, key_name, string])

    def db_getString(self, database_name, key_name):
        """
        Stores a string in the local database.
        """
        return self._call('db_getString', [database_name, key_name])

    def db_putHex(self, database_name, key_name, string):
        """
        Stores binary data in the local database.
        """
        return self._call('db_putHex', [database_name, key_name, string.encode('hex')])

    def db_getHex(self, database_name, key_name):
        """
        Returns binary data from the local database.
        """
        return self._call('db_getString', [database_name, key_name]).decode('hex')

    def shh_version(self):
        """
        Returns the current whisper protocol version.
        """
        return self._call('shh_version')

    def shh_post(self, topics, payload, priority, ttl, _from=None, to=None):
        """
        Sends a whisper message.
        ttl is time-to-live in seconds (integer)
        priority is integer
        """
        whisper_object = {
            'from': _from,
            'to': to,
            'topics': topics,
            'payload': payload,
            'priority': hex(priority),
            'ttl': hex(ttl)
        }
        return self._call('shh_post', [whisper_object])

    def shh_newIdentity(self):
        """
        Creates new whisper identity in the client.
        """
        return self._call('shh_newIdentity')

    def shh_hasIdentity(self, address):
        """
        Checks if the client hold the private keys for a given identity.
        """
        return self._call('shh_hasIdentity', [address])

    def shh_newGroup(self):
        """
        """
        return self._call('shh_hasIdentity')

    def shh_addToGroup(self):
        """
        """
        return self._call('shh_addToGroup')

    def shh_newFilter(self, to, topics):
        """
        Creates filter to notify, when client receives whisper message matching the filter options.
        """
        _filter = {
            'to': to,
            'topics': topics
        }
        return self._call('shh_newFilter', [_filter])

    def shh_uninstallFilter(self, filter_id):
        """
        Uninstalls a filter with given id. Should always be called when watch is no longer needed.
        Additionally Filters timeout when they aren't requested with shh_getFilterChanges for a period of time.
        """
        return self._call('shh_uninstallFilter', [filter_id])

    def shh_getFilterChanges(self, filter_id):
        """
        Polling method for whisper filters.
        """
        return self._call('shh_getFilterChanges', [filter_id])

    def shh_getMessages(self, filter_id):
        """
        Get all messages matching a filter, which are still existing in the node.
        """
        return self._call('shh_getMessages', [filter_id])






