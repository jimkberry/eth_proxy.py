#
#
import logging

import rlp
import utils
from pyeth_client.eth_utils import sha3
from pyeth_client.eth_txdata import TxData, UnsignedTxData
from eth_signer import EthereumSigner, EthSigDelegate
from bitcoin import encode_pubkey

# use bitcoin lib as a backup       
try:
    from c_secp256k1 import ecdsa_sign_raw, ecdsa_recover_raw
except ImportError:
#    import warnings
#    warnings.warn('missing c_secp256k1 falling back to pybitcointools')
    from bitcoin import ecdsa_raw_sign as ecdsa_sign_raw
    from bitcoin import ecdsa_raw_recover as ecdsa_recover_raw       
       
# Implements a sort of fake "signer" that will call 
# and ethereum node and ask it to do all the stuff
#
# TODO: Does this even work? I mean, it's only useful for nodes with unlocked
# accounts, so is not really production-capable anyway, but it's not
# completely clear that eth_sign() works at all. At least not for geth.
      

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
 
    def _do_sign_data(self, acct_addr, data):
        '''
?
        '''
        errmsg = None
        errcode = EthSigDelegate.SUCCESS
        all_accts = self.list_accounts()

        v_addr = utils.validate_address(acct_addr)
        if not v_addr:
            errmsg = 'Invalid account address: {0}'.format(acct_addr)
            errcode = EthSigDelegate.INVALID_ADDR
            
        if not errmsg:  
            if not v_addr in all_accts:
                errmsg = 'Account: {0} not in keystore'.format(v_addr)
                errcode = EthSigDelegate.UNKNOWN_ADDR                
                                 
        signature = None
        if not errmsg:
            signature = self.eth.eth_sign(v_addr, data)        
        
        return (signature, errcode, errmsg)
 
    def _do_recover_address(self, msg, sig):
        '''
        Given ahex-encoded hash string
        and a signature string (as returned from sign_data() or eth_sign())
        Return a string containing the address that signed it.
        '''
        errmsg = None
        errcode = EthSigDelegate.SUCCESS        
        addr_str = None
        try:
            v,r,s = utils.sig_to_vrs(sig)
            Q = ecdsa_recover_raw(msg, (v,r,s))
            pub = encode_pubkey(Q, 'bin')
            addr = sha3(pub[1:])[-20:]
            addr_str = '0x{0}'.format(addr.encode('hex'))
        except Exception as ex:
            errcode = EthSigDelegate.OTHER_ERROR
            errmsg = str(ex)
        return (addr_str, errcode, errmsg) 
 
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
        
    def sign_data(self, acct_addr, data, delegate=None, context_data=None): 
        '''
        Also allows for synchronous signing by not providing a delegate
        '''
        (sig, errcode, errmsg) = self._do_sign_data(acct_addr, data)
        if delegate:
            delegate.on_data_signed( context_data, sig, errcode, errmsg)
        else:
            return (sig, errcode, errmsg) 
         
    def recover_address(self, hash_str, signature, delegate=None, context_data=None): 
        '''
        Given a hash and a signature for it, returns the acct address that 
        did the signing.
        Signature is a single packed hex string
        Hash is a hex string
        Returned address is a hex string
        '''
        (addr, errcode, errmsg) = self._do_recover_address(hash_str, signature)
        if delegate:
            delegate.on_address_recovered( context_data, addr)
        else:
            return (addr, errcode, errmsg)          
        
