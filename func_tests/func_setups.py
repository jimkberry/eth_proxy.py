
import logging as log
import tempfile
import os
import codecs

from eth_proxy import eth_proxy_factory
from eth_proxy.node_signer import EthNodeSigner
from eth_proxy.solc_caller import SolcCaller

# I want logging to look like this
log.basicConfig(level=log.INFO,
                    format=('%(levelname)s:'
                                '%(name)s():'
                                '%(funcName)s():'
                                ' %(message)s'))
# don't want info logs from "requests" (there's a lot of 'em)
log.getLogger("requests").setLevel(log.WARNING)  
log.getLogger("urllib3").setLevel(log.WARNING)

class FuncSetups(object):
    
    def __init__(self, host_ip=None):
            self.eth_host = 'https://ropsten.infura.io:443'
            #eth_host = 'http://localhost:8545'
            #eth_host = 'ipc:/home/jim/cons-testnet-geth/data/geth.ipc'


    def create_proxy(self, host_ip=None):
        if not host_ip:
            host_ip = self.eth_host
        eth = eth_proxy_factory(host_ip)
        return eth


# If true, use a LocalKeystore implementation and the
# accounts specifed. Else, use an EthNodeSigner
# and the 1st no accounts it mananges (assume they are
# unlocked)


    def create_keystore(self, ks_type='EthLocalKeystore', ks_param=None):
        '''
        types: EthLocalKeystore (default), NodeSigner
        '''
        keystore = None
        if ks_type == 'EthLocalKeystore':
            # A keystore that manages accounts locally in files
            # that are interoperable with e geth keystore
            from eth_proxy.local_keystore import EthLocalKeystore        
            ks_path = '/home/jim/etherpoker/etherpoker/poker_keystore'
            if ks_param:
                ks_path = ks_param
            keystore = EthLocalKeystore(ks_path)
        
        elif ks_type == "EthNodeSigner":
            # A Keystore that is really the ethereum node
            # and has unlocked accounts
            # param is the eth_proxy object
            keystore = EthNodeSigner(ks_param)
        return keystore
    
    
    def get_account(self, keystore, acct_idx):
        # returns acct address
        if keystore.__class__.__name__ == 'EthLocalKeystore':    
            accounts = keystore.list_accounts()
            # print("eth_accounts(): {0}".format(accounts))            
            pw = 'foo'
            acct = accounts[acct_idx]
            errmsg = keystore.unlock_account(acct, pw)
            if errmsg:
                print("Error unlocking acct: {0} \nMsg: {1}.".format(acct, errmsg))
                return None
            print('Account unlocked.')    
        else:
            accounts = keystore.list_accounts()
            print("eth_accounts(): {0}".format(accounts))
            acct = accounts[acct_idx]
        return acct
    
    def write_temp_contract(self, file_name, src_code):
        '''
        Creates a file in the sys tempdir
        containing the provided src. 
        This is just here to allow testcode to contain
        contract source code inline. 
        '''
        f_path = os.path.join(tempfile.gettempdir(), file_name)
        with codecs.open(f_path, 'w', 'utf8') as f:
            f.write(src_code)           
        return f_path
        

