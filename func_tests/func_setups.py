
import logging as log

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


# The node
eth_host = 'https://consensysnet.infura.io:8545'
#eth_host = 'http://localhost:8545'
#eth_host = 'ipc:/home/jim/cons-testnet-geth/data/geth.ipc'

def create_proxy():
    eth = eth_proxy_factory(eth_host)
    return eth


# If true, use a LocalKeystore implementation and the
# accounts specifed. Else, use an EthNodeSigner
# and the 1st no accounts it mananges (assume they are
# unlocked)
USE_LOCAL_KEYSTORE = True


def create_keystore(proxy):
    if USE_LOCAL_KEYSTORE:
        #
        # A keystore that manages accounts locally in files
        # that are interoperable with e geth keystore
        #
        from eth_proxy.local_keystore import EthLocalKeystore
        keystore_path = '/home/jim/etherpoker/etherpoker/poker_keystore'
        keystore = EthLocalKeystore(keystore_path)
    else:
        # A Keystore that is really the ethereum node
        keystore = EthNodeSigner(proxy)
    return keystore
    
    
def get_account(keystore, acct_idx):
    # returns acct address
    if USE_LOCAL_KEYSTORE:    
        accounts = ['0x43f41cdca2f6785642928bcd2265fe9aff02911a',
                    '0x510c1ffb6d4236808e7d54bb62741681ace6ea88']
        pw = 'foo'
        acct = accounts[acct_idx]
        errmsg = keystore.unlock_account(acct, pw)
        if errmsg:
            print("Error unlocking acct: {0} \nMsg: {1}.".format(acct, errmsg))
            return None
        print('Account unlocked.')    
    else:
        accounts = keystore.list_accounts()
        print("\neth_accounts(): {0}".format(accounts))
        acct = accounts[acct_idx]
    return acct




