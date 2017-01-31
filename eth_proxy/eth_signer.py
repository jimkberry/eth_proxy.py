#
#
class EthereumSigner(object):
    '''
     Mixin to define an API that a class can use to declare that
     it is capable of signing an Ethereum transaction or data
    '''

    def sign_transaction(self, acct_addr, unsigned_tx, delegate=None, context_data=None):
        '''        
        Params:
            acct_addr - etherem account hex address
            unsigned_tx -  RLP-encoded raw unsigned tx (hex string)
            delegate - A class implementing the EthSigDelegate mixin.
            context_data - data passed back to the delegate unchanged
                
        Returns: (signed_tx_str, errcode, errmsg) 
        '''
        raise NotImplementedError()
    
    def sign_data(self, acct_addr, data_hash, delegate=None, context_data=None):
        '''
        
        Params:
            acct_addr - etherem account hex address
            data_hash -  a 32 byte hash
            delegate - A class implementing the EthSigDelegate mixin.
            context_data - data passed back to the delegate unchanged
                
        Returns: (signature, errcode, errmsg) 
        '''
        raise NotImplementedError()

    def recover_address(self, hash_str, signature, delegate=None, context_data=None): 
        '''
        Asynchronous - returns nothing and results come via the delegate        

        Signature is a single packed hex string
        Hash is a hex string
        Recovered address is a hex string
        
        Returns: (acct_addr, errcode, errmsg)
        '''
        raise NotImplementedError()
        


class EthSigDelegate(object):
    '''
    Mixin defining API needed by a class that wishes to
    callEthereumSigner.sign_transaction()
    '''
    
    SUCCESS = 0
    INVALID_ADDR = -1
    UNKNOWN_ADDR = -2
    ADDR_LOCKED = -3
    OTHER_ERROR = -10
    
    def on_transaction_signed(self, context_data, signed_tx, result_code, err_msg=None):        
        '''
        Params:
            contxt_data - data passed in when sign_transaction() was called
            signed_tx - signed transaction, suitable for eth_sendRawTransaction()
            result_code - constant defined above
            err_msg - optional information
        '''
        raise NotImplementedError()
    
    def on_data_signed(self, context_data, signature, result_code, err_msg=None):        
        '''
        Params:
            contxt_data - data passed in when sign_transaction() was called
            signature - 134 byte signature string
            result_code - constant defined above
            err_msg - optional information
        '''
        raise NotImplementedError()    
    
    def on_address_recovered(self, context_data, addres_str, result_code, err_msg=None):        
        '''
        Params:
            contxt_data - data passed in when sign_transaction() was called
            address_str - hex-encoded address string
            result_code - constant defined above
            err_msg - optional information
        '''
        raise NotImplementedError()     
    
