#
#
import logging
import os
import json
import codecs
import datetime as dt

import rlp
import utils
from pyeth_client.eth_utils import int_to_bytes
from pyeth_client.eth_txdata import TxData, UnsignedTxData
import pyeth_client.eth_keys as keys
from tx_signer import EthereumTxSigner, EthTxSigDelegate
       
#
# Implements a synchronous local keystore and then, just to use as an example,
# an async implementation of the same keystore
#       
       

class EthereumKeystore(EthereumTxSigner):
    '''
    Stores encrypted account info as json files inside
    a directory. 1 file per account.
    Uses same format as pyethereum/geth/(and eth, too?)
    
    In other words - if you are running geth on the local machine you can read/use
    the geth keystore.
    
    Not sure if actually doing that that is a good idea or not, though. 
    '''
    
    def __init__(self, directory_path):
        '''
        The contract descriptor is a json file which acts as an
        adjunct to a contract source file
        '''
        self.log = logging.getLogger(__name__)           
        self._accounts = {}
        self._cached_pks = {}
        self._directory_path = directory_path
        self.load_accounts()
      
    def load_accounts(self):
        '''
        Read in json data for all accounts in folder.
        
        '''
        if not self._directory_path:
            raise( RuntimeError("No keystore path specified. Can only use unlocked accounts."))
        
        # Ensure directory is there
        try: 
            os.makedirs(self._directory_path)
        except OSError:
            if not os.path.isdir(self._directory_path):
                raise
                  
        filePaths  = os.listdir(self._directory_path) 
        for fPath in filePaths:
            fullPath = os.path.join(self._directory_path, fPath)
            with open(fullPath) as f:
                acctData = json.load(f)                               
                if keys.check_keystore_json(acctData):
                    addrStr = utils.validate_address(acctData.get('address'))
                    self._accounts[addrStr] = acctData
                    
                    
    def write_account(self, address):
        '''
        Write a keystore file into the folder
        Use geth-ish naming conventions
        '''
        acctData = self._accounts.get(address)
        fname = "{0}_{1}".format(dt.datetime.utcnow().strftime('%Y%m%dT%H%M%S'), address)
        path = os.path.join(self._directory_path, fname)
        
        with codecs.open(path, 'w', 'utf8') as f:
            f.write(json.dumps(acctData, ensure_ascii=False))        
       
    def list_accounts(self):
        '''
        List of addresses
        '''
        return self._accounts.keys()

    def new_account(self, password):
        '''
        Create a new account.
        Returns address
        '''
        priv_key = keys.new_priv_key()
        
        # try scrypt first
        try:
            acct_data = keys.make_keystore_json(priv_key, password, kdf='scrypt')
        except:
            acct_data = keys.make_keystore_json(priv_key, password, kdf='pbkdf2')            
        
        addrStr = utils.validate_address(acct_data.get('address'))
        self._accounts[addrStr] = acct_data
        self.write_account(addrStr)
        return addrStr

    def unlock_account(self, acct_addr, password):
        '''
        look for acct addr and recover the private key
        and cache it.
        returns rrMsg        
        '''
        priv_key = None
        errmsg = None
        v_addr = utils.validate_address(acct_addr)
        if not v_addr:
            errmsg = 'Invalid account address: {0}'.format(acct_addr)

        if not errmsg:
            acct_data = self._accounts.get(v_addr)
            if not acct_data:
                errmsg = 'Account: {0} not in keystore'.format(v_addr)
                
        if not errmsg:
            try:
                priv_key = keys.decode_keystore_json(acct_data, password)
            except:
                errmsg = 'Password failed for account: {0}'.format(v_addr)
                  
        if priv_key:
            self._cached_pks[v_addr] = priv_key
                  
        return errmsg             
   
    def _do_sign_transaction(self, acct_addr, unsigned_tx_str):
        '''
        Make sure account is in the keystore and unlocked, then sign the tx
        unsigned_tx_str is hex-encoded. probably starts with '0x'
        returns: (signed_tx, result_code, msg) 
        '''
        priv_key = None
        errmsg = None
        errcode = EthTxSigDelegate.SUCCESS

        v_addr = utils.validate_address(acct_addr)
        if not v_addr:
            errmsg = 'Invalid account address: {0}'.format(acct_addr)
            errcode = EthTxSigDelegate.INVALID_ADDR
            
        if not errmsg:
            acct_data = self._accounts.get(v_addr)
            if not acct_data:
                errmsg = 'Account: {0} not in keystore'.format(v_addr)
                errcode = EthTxSigDelegate.UNKNOWN_ADDR                
                
        if not errmsg:
            priv_key = self._cached_pks.get(v_addr)
            if not priv_key:
                errmsg = 'Account locked: {0}'.format(v_addr)
                errcode = EthTxSigDelegate.ADDR_LOCKED 
                  
        signed_tx = None
        if priv_key:
            utx = TxData.createFromTxData(unsigned_tx_str)
            signed_tx = utx.getSignedTxData(int_to_bytes(priv_key))
        
        return (signed_tx, errcode, errmsg)
 
    # EthereumTxSigner API  
    def sign_transaction(self, acct_addr, unsigned_tx_str, delegate=None, context_data=None): 
        '''
        This particular implementation allows for synchronous signing by not providing a delegate
        '''
        (signed_tx, errcode, errmsg) = self._do_sign_transaction(acct_addr, unsigned_tx_str)
        if delegate:
            delegate.on_transaction_signed( context_data, signed_tx, errcode, errmsg)
        else:
            return (signed_tx, errcode, errmsg)  
 
# TODO: delete
#
#     def sign_transaction_sync(self, acct_addr, unsigned_tx):
#         return self._do_sign_transaction(acct_addr, unsigned_tx)        
#  
 
class AsyncKeystore(EthereumKeystore):
    '''
    This is a completely contriived async-ification of the EthereumKeystore
    It's reall for testing and its asyncness comes from being polled by
    some ecternal controller
    
     
    '''
    def __init__(self, directory_path):
        super(AsyncKeystore, self).__init__(directory_path)
        self._jobs = []
    
    def loop(self):
        '''
        Pop one off - sign it
        '''
        while len(self._jobs):
            job = self._jobs.pop()
            self._sign_transaction(job['acct'],job['tx'],job['delegate'],job['context'])
        

    def sign_transaction(self, acct_addr, unsigned_tx_str, delegate=None, context_data=None):
        '''
        Make sure account is in the keystore and unlocked, then sign the tx
        unsigned_tx_str is hex-encoded. probably starts with '0x'
        '''    
        if not delegate:
            raise RuntimeError("Async keystore requires delegate")
        
        job = { 'acct': acct_addr,
                'tx': unsigned_tx_str,
                'context': context_data,
                'delegate': delegate }
        
        self._jobs.append(job) 
        return None
        
        
    def _sign_transaction(self, acct_addr, unsigned_tx_str,delegate, context_data):
        '''
        Make sure account is in the keystore and unlocked, then sign the tx
        unsigned_tx_str is hex-encoded. probably starts with '0x'
        '''            
        priv_key = None
        errmsg = None
        errcode = EthTxSigDelegate.SUCCESS

        v_addr = utils.validate_address(acct_addr)
        if not v_addr:
            errmsg = 'Invalid account address: {0}'.format(acct_addr)
            errcode = EthTxSigDelegate.INVALID_ADDR
            
        if not errmsg:
            acct_data = self._accounts.get(v_addr)
            if not acct_data:
                errmsg = 'Account: {0} not in keystore'.format(v_addr)
                errcode = EthTxSigDelegate.UNKNOWN_ADDR                
                
        if not errmsg:
            priv_key = self._cached_pks.get(v_addr)
            if not priv_key:
                errmsg = 'Account locked: {0}'.format(v_addr)
                errcode = EthTxSigDelegate.ADDR_LOCKED 
                  
        signed_tx = None
        if priv_key:
            utx = TxData.createFromTxData(unsigned_tx_str)
            signed_tx = utx.getSignedTxData(int_to_bytes(priv_key))
        
        if delegate:        
            delegate.on_transaction_signed(context_data, signed_tx, errcode, errmsg)
        
        return (signed_tx, errcode, errmsg)
 
        
