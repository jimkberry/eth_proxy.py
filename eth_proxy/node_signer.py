#
#
import logging
import os
import json
import codecs
import datetime as dt

import rlp
import utils
from pyeth_client.eth_utils import int_to_bytes, sha3
from pyeth_client.eth_txdata import TxData, UnsignedTxData
from eth_signer import EthereumSigner, EthSigDelegate
       
#
# Implements a sort of fake "signer" that will call 
# and ethereum node and ask it to do all the stuff
#
#       
       

class EthNodeSigner(EthereumSigner):
    '''
    Talks to an ethereum node and gets information about accounts that it manages
    and also asks it to sign transactions
    '''
    def __init__(self, eth_proxy):
        '''
        eth_proxy is an instance of an eth_proxy object
        '''
        self.log = logging.getLogger(__name__)           
        self.eth = eth_proxy
    
    def list_accounts(self):
        '''
        List of addresses
        '''
        addrs = self.eth.eth_accounts()
        return addrs
         
    def _do_sign_transaction(self, acct_addr, unsigned_tx_str):
        '''
        Queries a running node.
        '''
        errmsg = None
        errcode = EthSigDelegate.SUCCESS
        all_accts = self.list_accounts()
        signed_tx = None

        v_addr = utils.validate_address(acct_addr)
        if not v_addr:
            errmsg = 'Invalid account address: {0}'.format(acct_addr)
            errcode = EthSigDelegate.INVALID_ADDR
            
        if not errmsg:  
            if not v_addr in all_accts:
                errmsg = 'Account: {0} not in keystore'.format(v_addr)
                errcode = EthSigDelegate.UNKNOWN_ADDR                
                
        if not errmsg:
            tx = TxData.createFromTxData(unsigned_tx_str)
            rawhash = sha3(rlp.encode(tx, UnsignedTxData))
            rh_str = '0x{0}'.format(rawhash.encode('hex'))
            sig = self.eth.eth_sign(v_addr, rh_str)
            v,r,s = utils.sig_to_vrs(sig)
            signed_tx = tx.getSignedTxData(v,r,s)
 
        return (signed_tx, errcode, errmsg)
 
    # EthereumSigner API  
    def sign_transaction(self, acct_addr, unsigned_tx_str, delegate=None, context_data=None): 
        '''
        This particular implementation allows for synchronous signing by not providing a delegate
        '''
        (signed_tx, errcode, errmsg) = self._do_sign_transaction(acct_addr, unsigned_tx_str)
        if delegate:
            delegate.on_transaction_signed( context_data, signed_tx, errcode, errmsg)
        else:
            return (signed_tx, errcode, errmsg)  
        
        
