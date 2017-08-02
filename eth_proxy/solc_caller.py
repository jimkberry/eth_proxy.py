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
    def call_solc(source_path, solc_args, contract_name):
        '''
        Do the things common to generating metadata and simple compilation
        '''
        oldCwd = os.getcwd();
        newDir = os.path.dirname(source_path)
        os.chdir(newDir)        

        local_source_path = "./{0}".format(os.path.basename(source_path))
        solc_args.append(local_source_path)
                
        results = {'contract_name': None, 'abi': None, 'bin': None}
        jdata = None
        try:
            solc_results = SolcCaller._call_solc(solc_args)
            jdata = json.loads(solc_results)   
        except:
            log.error("call_solc() failed: {0}".format(sys.exc_info()[0]))
                                           
        os.chdir(oldCwd) 
                    
        if contract_name is not None:        
            key = "{0}:{1}".format(local_source_path,contract_name) 
            con_data = jdata['contracts'].get(key)
            if not con_data:
                log.error("call_solc() contract: {0} not found".format(contract_name))                
            
        else:
            log.warning("No contract name specified. Using first in source file.") 
            log.warning("Calling compile_solidity() without contract name is deprecated. Please update your code.")
            con_data = jdata['contracts'].values()[0]
            contract_name = jdata['contracts'].keys()[0]
            
        if con_data:            
            results['contract_name'] = contract_name
            results['bin'] = con_data.get('bin')
            # solc packs the ABI data into a single json string  
            if con_data.get('abi'):
                results['abi'] = json.loads(con_data.get('abi'))
                      
        return results            
                      
         
    @staticmethod
    def compile_solidity(source_path, contract_name=None):
        '''
        Changes to solc can to break pyethereum's solc wrapper, and we're not really
        using it to do much. So let's just do it here. Most of this is pretty much lifted from
        pyethereum/_solidity
        '''
        args = ['solc', '--combined-json', 'bin']         
        result = None                    
        con_data = SolcCaller.call_solc(source_path, args, contract_name)
        if con_data.get('bin'):             
            result = con_data.get('bin').decode('hex')                     
        return result
        
    @staticmethod        
    def generate_metadata(source_path, contract_name=None):
        '''
        This assumes a newer version of solc than _compile_solidity() assumed
        when it was written, so the arg-building process is not so weird.
        '''
        args = ['solc', '--combined-json', 'abi,bin']
        results = SolcCaller.call_solc(source_path, args, contract_name) 
        return results
                

