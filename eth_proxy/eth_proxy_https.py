#
#
from eth_proxy_base import EthProxyBase
import requests
import json


class EthProxyHttps(EthProxyBase):
    '''
    EthProxy implemented using json-rpc over HTTPS
    
    See EthProxyBase for details.
    '''

    def __init__(self, rpc_host, rpc_port):
        super(EthProxyHttps, self).__init__()        
        self.rpc_host = rpc_host
        self.rpc_port = rpc_port
        

    #
    # Internal stuff
    #
    def _call(self, method, params=None, _id=0):
        '''
        Actually execute the RPC call and field the result
        '''
        params = params or []
        data = json.dumps({
            'jsonrpc': '2.0',
            'method': method,
            'params': params,
            'id': _id
        })
               
               
        response = requests.post("https://{0}:{1}".format(self.rpc_host, self.rpc_port), data=data).json()

        if 'result' in response:
            return response['result']
        else:
            raise RuntimeError('Error from RPC call. Returned payload: {0}'.format(response))



