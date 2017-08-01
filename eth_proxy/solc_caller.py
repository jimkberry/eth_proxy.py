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
    def go_to_source_folder(source_path):
        '''
        Extract the dir part of the source file path and set cwd there.
        Return val is dir where we were when we started. We want to do this because solc
        (currently) inserts the source file name and path into places in the
        compiled code where a library address later needs to be linked in. 
        More than 40 characters (length of a hex-encoded address) causes real 
        problems, so it's best if the folder path is './'
        '''
        oldDir = os.getcwd();
        newDir = os.path.dirname(source_path)
        os.chdir(newDir)
        return oldDir         
         
    @staticmethod
    def compile_solidity(source_path, contract_name=None):
        '''
        Changes to solc can to break pyethereum's solc wrapper, and we're not really
        using it to do much. So let's just do it here. Most of this is pretty much lifted from
        pyethereum/_solidity
        
        TODO: Deal with the duplicate-ish nature of this vs geterate_metadata()
        Factor out the setup and teardown, which are essentialy the same.
        
        '''

        # W need to be in the same folder as the source file in order to minimize
        # the length of the string that gets inserted into the output when a library is referenced,
        # since solc inserts the path aas well as the file and contract names.
        # it's really easy to be longer then the 40 character length of a hex-encoded address
        oldCwd = SolcCaller.go_to_source_folder(source_path)
        log.info("Compiling from {0}".format(os.getcwd()))        
        
        local_source_path = "./{0}".format(os.path.basename(source_path))        
        log.info("Source {0}".format(local_source_path))        
          
        args = ['solc', '--combined-json', 'bin', local_source_path]  # changed to "bin" in 0.1.2
                              
        #
        # This is for eth_contract metadata generation
        #
        result = None
        try:
            solc_results = SolcCaller._call_solc(args)
            jdata = json.loads(solc_results)   
        except:
            log.error("compile_solidity() failed: {0}".format(sys.exc_info()[0]))
            
        if contract_name is not None:        
            key = "{0}:{1}".format(local_source_path,contract_name) 
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
                       
                       
        os.chdir(oldCwd)                       
        return result
        
    @staticmethod        
    def generate_metadata(source_path, contract_name):
        '''
        This assumes a newer version of solc than _compile_solidity() assumed
        when it was written, so the arg-building process is not so weird.
        '''
        oldCwd = SolcCaller.go_to_source_folder(source_path)
        log.info("Compiling from {0}".format(os.getcwd()))        
        
        local_source_path = "./{0}".format(os.path.basename(source_path))        
        log.info("Source {0}".format(local_source_path))        
        
        args = ['solc', '--combined-json', 'abi,bin', local_source_path]
        results = None
        try:
            solc_results = SolcCaller._call_solc(args)                
            jdata = json.loads(solc_results)
            # TODO: we can only handle a single contract per file

            key = "{0}:{1}".format(local_source_path,contract_name)
            con_data = jdata['contracts'][key]
            
            # solc packs the ABI data into a single string  
            bin_data = con_data['bin']
            abi_data = json.loads(con_data['abi']) 
            results = {'contract_name': contract_name, 'abi': abi_data, 'bin': bin_data}
        except:
            log.warning("generate_solc_metadata() failed: {0}".format(sys.exc_info()[0]))

        os.chdir(oldCwd)   
        return results
                

