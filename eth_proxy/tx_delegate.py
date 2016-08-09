#
#

class TransactionDelegate(object):
    '''
    Use this as a mixin and implement contract_created() or tx_complete()
    then pass the instance to create_contract_async(), or send_tx_async()
    Make sure do_poll() or is getting called
    
    Note: "delegate_info" is a tuple of the form (delegateObject,delegateData) where delegateData is passed back to 
    the object - usually to distinguish between different calls handled by the same delegate.
    
    Also note that methods that take delegateInfo can take either a single tuple, or an LIST of tuples if there
    is a desire that more than one delegate be notified. Notifications will be in the list's order.
    '''
    
    # return status
    RESULT_SUCCESS = 0
    RESULT_TIMEOUT = -1
    RESULT_CALCELLED = -2
    RESULT_FAILURE = -3
    
   
    def tx_submitted(self, delegate_data, tx_hash, err_code, err_msg):
        '''
        Because transaction submission might require an asynchronous signing step,
        the EthProxy methods that submit transaction (and create contracts) will in general
        not have completed the task when they return.
        
        This method is called when the signed tx is actually submitted (so we have a tx hash)
        or has failed.
        '''
        raise RuntimeError('Not implemented')
   
    def tx_complete(self, delegate_data, tx_hash, contract_addr, has_code,
                    gas_price, gas_used, err, err_msg):
        '''
        Called when transaction is found in the current block.
        delegate_data is what you passed into create_contract_async()
        '''
        raise RuntimeError('Not implemented')


