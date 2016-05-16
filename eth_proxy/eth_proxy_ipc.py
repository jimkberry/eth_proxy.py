#
#
from eth_proxy_base import EthProxyBase
import socket
import json

class EthProxyIpc(EthProxyBase):
    '''
    EthProxy implemented using json-rpc over HTTP
    
    See EthProxyBase for details.
    '''

    def __init__(self, ipc_path):
        super(EthProxyIpc, self).__init__()   
        
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.connect(ipc_path)
        self.socket.settimeout(2)        

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
               

        response = ''
        self.socket.sendall(data)
        while True:
            try:
                response += self.socket.recv(4096)
            except socket.timeout:
                break
        if response == "":
            raise ValueError("No JSON returned by socket")
        response = json.loads(response)        
                        
 
        if 'result' in response:
            return response['result']
        else:
            raise RuntimeError('Error from RPC call. Returned payload: {0}'.format(response))



