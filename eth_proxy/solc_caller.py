#
# Horrible name. 
#
import logging as log
import sys
import time
from types import ListType
import json
import re
import subprocess
import os

class SolcCaller(object):
    '''
    Just calls solc on a source file - assumes it is installed on the local machine
    '''
                   
    @staticmethod
    def _call_solc(args):
        '''
        Just calls solc on the given source with the given args
        Note that "solc" is the first arg
        '''    
        p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        (stdoutdata, stderrdata) = p.communicate()
        if p.returncode:
            raise RuntimeError('solc compilation failed')
        return stdoutdata
        
         
    @staticmethod
    def compile_solidity(source_path, contract_name=None):
        '''
        Changes to solc can to break pyethereum's solc wrapper, and we're not really
        using it to do much. So let's just do it here. Most of this is pretty much lifted from
        pyethereum/_solidity
        '''

        args = ['solc', '--combined-json', 'bin', source_path]  # changed to "bin" in 0.1.2
                              
        #
        # This is for eth_contract metadata generation
        #
        #if generate_metatdata:  # note that this is assuming a newer version of solc
        #    args = ['solc', '--combined-json', 'abi,bin']
                              
        # you end up with "{u'contracts': {u'EtherPokerTable': {u'bin': u'60606040527...'}}}"
        # and you get the hex data (no, there's no solc option for just the data)
        # NOTE: I don't think this is true anymore - but's it's not broke...
        result = None
        try:
            solc_results = SolcCaller._call_solc(args)
            jdata = json.loads(solc_results)   
        except:
            log.error("compile_solidity() failed: {0}".format(sys.exc_info()[0]))
            
        if contract_name is not None:        
            key = "{0}:{1}".format(source_path,contract_name) 
            c_data = jdata['contracts'].get(key)
            if not c_data:
                log.error("compile_solidity() contract: {0} not found".format(contract_name))                
            
        else:
            log.warning("No contract name specified. Using first in source file.") 
            log.warning("Calling compile_solidity() without contract name is deprecated. Please update your code.")
            c_data = jdata['contracts'].values()[0]                            
            
        if c_data:            
            hx = c_data['bin']                
            result = hx.decode('hex')
                       
        return result
        
    @staticmethod        
    def generate_metadata(source_path, contract_name):
        '''
        This assumes a newer version of solc than _compile_solidity() assumed
        when it was written, so the arg-building process is not so weird.
        '''
        args = ['solc', '--combined-json', 'abi,bin', source_path]
        results = None
        try:
            solc_results = SolcCaller._call_solc(args)                
            jdata = json.loads(solc_results)
            # TODO: we can only handle a single contract per file

            key = "{0}:{1}".format(source_path,contract_name)
            con_data = jdata['contracts'][key]
            
            # solc packs the ABI data into a single string  
            bin_data = con_data['bin']
            abi_data = json.loads(con_data['abi']) 
            results = {'contract_name': contract_name, 'abi': abi_data, 'bin': bin_data}
        except:
            log.warning("generate_solc_metadata() failed: {0}".format(sys.exc_info()[0]))

        return results
                

