#
#
import time
import codecs

def hex_str_to_int(hexStr):
    '''
    TODO: Is there a more "official" way to do this?
    '''
    if hexStr[:2] == '0x':
        hexStr = hexStr[2:]
    return int(hexStr,16)

def bytes_to_str(byte_array):
    '''
    If a function returns, say, a 'bytes32' and you just want a string.
    Otherwise it will be a zero-right-padded string of length N (for "bytes<n>")
    '''
    return ''.join([byte_array[i] for i in xrange(len(byte_array)) if byte_array[i] != '\x00'])
    
def hex_to_str(hexStr):
    '''
    Mostly for unpacking string (or string bytes32) values from
    JSON transaction log entries. The data is a string, but is:
    Something like:
    "0x47616d652046756c6c0000000000000000000000000000000000000000000000"
    instead of "Game Full", which is what we want.
    '''
    if hexStr[0:2] == '0x':   
        hexStr = hexStr[2:]
    return  codecs.decode(hexStr, "hex").rstrip('\x00')

def validate_address(addr_str):
    '''
    Prepend '0x' to address if not there
    Returns:
      addr_str if valid
      None  if invalid
    '''
    addr_str = addr_str.strip() # don't penalize for whitespace
    if addr_str[0:2] != '0x':
        addr_str = "0x{0}".format(addr_str)  
    # is the passed-in account even remotely valid?
    try:
        if (len(addr_str) != 42) or (hex_str_to_int(addr_str) == 0):
            addr_str = None
    except ValueError as vx:
        # Hmmm. Seems a waste not to have at least logging in here.
        addr_str = None
            
    return addr_str

class EthTestTimer(object):
    '''
    This is a utility class to make it easy to time events (like, say, the amount
    of time it takes for a TX to get into the chain) and display time and block stats
    '''

    def __init__(self, eth_wrapper):
        '''
        '''
        self.eth = eth_wrapper
        self.ts_start = 0
        self.ts_mark = 0
        self.start_blocknum = 0
        self.mark_blocknum = 0        
        self.start()

    def _int_cur_blocknum(self):
        blockStr = self.eth.passthru.eth_blockNumber()
        return int(blockStr,0)

    def start(self):
        '''
        Called automatically on init, start()
        can be called again to reset the timer
        '''
        self.start_blocknum = self._int_cur_blocknum()
        self.ts_start = time.time()

    def mark(self):
        '''
        mark the end of a timing period (start is still valid)
        if you call mark() again the previous start is still used
        returns results tuple
        '''
        self.mark_blocknum = self._int_cur_blocknum()
        self.ts_mark = time.time()
        return self.results()   

    def results(self):
        '''
        call after mark() to get elapsed time, elapsed blocks, and
        secs/block during the period
        returns tuple: (elapsed_secs, blocks, secs_per_block)
        '''
        elapsed_secs = self.ts_mark - self.ts_start
        blocks = self.mark_blocknum - self.start_blocknum 
        secs_per_block = elapsed_secs / float(blocks) if blocks else 0   
        return (elapsed_secs, blocks, secs_per_block)

        