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
    def compile_solidity(source_path):
        '''
        Changes to solc can to break pyethereum's solc wrapper, and we're not really
        using it to do much. So let's just do it here. Most of this is pretty much lifted from
        pyethereum/_solidity
        
        Note that this assumes there is only 1 contract in the source code
        
        Keep in mind that solc version numbering is inconsistent, so you can't turn the version
        into a numeric value and compare < and >
        '''
        version_info = subprocess.check_output(['solc', '--version'])
        match = re.search("^Version: ([0-9a-zA-Z.+-]+)", version_info, re.MULTILINE)
        assert(match)
        vstr = match.group(1)    

        if vstr[:5] == '0.1.1':
            args = ['solc', '--combined-json', 'binary', source_path]
        else:
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
                    
            # API changes with version. Sigh.
            if vstr[:5] == '0.1.1':
                hx = jdata['contracts'].items()[0][1]['binary']
            else:
                hx = jdata['contracts'].items()[0][1]['bin']            
    
            # print '[{0}]'.format(hx)
            result = hx.decode('hex')
        except:
            pass  # TODO: Log a warning
                       
        return result
        
    @staticmethod        
    def generate_metadata(source_path):
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
            
            con1_name = jdata['contracts'].keys()[0]
            con1_data = jdata['contracts'].items()[0][1]
            # solc packs the ABI data into a single string
            bin_data = con1_data['bin']
            abi_data = json.loads(con1_data['abi']) 
            results = {'contract_name': con1_name, 'abi': abi_data, 'bin': bin_data}
        except:
            log.warning("generate_solc_metadata() failed: {0}".format(sys.exc_info()[0]))

        return results
                

