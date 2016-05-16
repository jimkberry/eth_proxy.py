
from eth_proxy_http import EthProxyHttp
from eth_proxy_https import EthProxyHttps
from eth_proxy_ipc import EthProxyIpc
from tx_delegate import TransactionDelegate
from eth_contract import EthContract
from solc_caller import SolcCaller
from node_signer import EthNodeSigner

import urlparse

def eth_proxy_factory(nodeURI):
    '''
    Parse a URI and depending on the scheme choose and create
    an eth_proxy implementation 
    '''
    result = urlparse.urlparse(nodeURI)
    scheme = result.scheme or 'http'
    host = result.netloc.split(':')[0]
    path = result.path
    port = result.port
    
    proxy  = None
    if scheme == 'http':
        proxy = EthProxyHttp(host,port)
    elif scheme == 'https':
        proxy = EthProxyHttps(host,port)
    elif scheme == 'ipc':
        proxy = EthProxyIpc(path)          
    return proxy