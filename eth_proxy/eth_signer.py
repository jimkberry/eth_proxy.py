#
#
class EthereumSigner(object):
    '''
     Mixin to define an API that a class can use to declare that
     it is capable of signing an Ethereum transaction  
    '''

    def sign_data(self, acct_addr, data, delegate, context_data):
        '''
        Asynchronous - returns nothing and results come via the delegate
        
        Params:
            acct_addr - etherem account hex address
            unsigned_tx -  data to sign
            delegate - A class implementing the EthSigDelegate mixin.
            context_data - data passed back to the delegate unchanged
                
        Returns: Nothing 
        '''
        raise NotImplementedError()

    
    def sign_transaction(self, acct_addr, unsigned_tx, delegate, context_data):
        '''
        Asynchronous - returns nothing and results come via the delegate
        
        Params:
            acct_addr - etherem account hex address
            unsigned_tx -  RLP-encoded raw unsigned tx
            delegate - A class implementing the EthSigDelegate mixin.
            context_data - data passed back to the delegate unchanged
                
        Returns: Nothing 
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
    
