#
#
from eth_proxy_base import EthProxyBase
import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import json

class EthProxyHttp(EthProxyBase):
    '''
    EthProxy implemented using json-rpc over HTTP
    
    See EthProxyBase for details.
    
    TODO: Too much copy/paste similarity between HTTP and HTTPS implementations    
    '''

    def __init__(self, rpc_host, rpc_port):
        super(EthProxyHttp, self).__init__()        
        self.rpc_host = rpc_host
        self.rpc_port = rpc_port
        self.timeout = (6.09, 12.0) 
        self.session = self._setup_session()
        
        
    def _setup_session(self):
        s = requests.Session()

        retries = Retry(total=10,
                        backoff_factor=0.1,
                        connect=5,
                        read=5,
                        status_forcelist=[ 500, 502, 503, 504 ])

        s.mount('http://', HTTPAdapter(max_retries=retries))        
        return s
        
    #
    # Internal stuff
    #
    def _call(self, method, params=None, _id=0):
        '''
        Actually execute the RPC call and field the result
        '''
        #self.log.info("Eth Node request: {0}".format(method))        
        params = params or []
        data = json.dumps({
            'jsonrpc': '2.0',
            'method': method,
            'params': params,
            'id': _id
        })
                         
                         
        headers = {'Content-Type': 'application/json'}
        
        url = "http://{0}:{1}".format(self.rpc_host, self.rpc_port)
                         
        response = self.session.post(url, timeout=self.timeout, headers=headers, data=data) 

        if 'result' in response:
            return response['result']
        else:
            raise RuntimeError('Error from RPC call. Returned payload: {0}'.format(response))



