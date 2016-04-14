#
#
import logging
import sys
from eth_proxy_base import EthProxyBase

#
# TODO: move to it's own module after refactoring this out
#
class EthAccount(object):
    '''
    You can communicate with ethereum and do useful things without
    involving an account - but only a few.
    
    This class holds the account-specific information needed by eth_proxy.
    
    The model is that an EthProxy instance is created with no account info,
    that an account instance can be "attached" to it when needed, and detached
    and/or replaced without having to re-create the EthProxy.
    
    TODO: nonce handling has a hole, in that it's possible that a tx will not 
    picked up by a miner, in which case we will be submitting nonces that are too large,
    which will be silently accepted and  - well - I dunno what happens to em
    
    '''
    def __init__(self, address, priv_key):
        '''
        Currently, address is a hex address hash (not ICAN, yet)
        '''
        self.log = logging.getLogger(__name__)              
        self._addr = address
        self._priv_key = priv_key  #might stay None if using an unlocked acct
        self._nonce = None # Note that we need to maintain the nonce in this class
        
    def address(self):
        return self._addr
    
    def priv_key(self):
        return self._priv_key
        
    def nonce(self, eth_proxy):
        '''
        If nonce isn't set get it from the node
        '''
        if self._nonce is None:
            self._nonce = eth_proxy.eth_getTransactionCount(self._addr, 'latest')
        self.log.info("Nonce: {0} ".format(self._nonce))
        return self._nonce
    
    def increment_nonce(self):
        '''
        Call this when a tx has been successfully submitted.
        '''
        self._nonce += 1    
    
