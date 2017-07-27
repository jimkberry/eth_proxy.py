
import logging as log
import time
from func_setups import FuncSetups



fs = FuncSetups()


eth_rop = fs.create_proxy('https://ropsten.infura.io:443')
eth_inf = fs.create_proxy()

keystore = fs.create_keystore()
account = fs.get_account(keystore, 0)
account2 = fs.get_account(keystore, 1)


def prep_n_sign_tx(nonce, value):
    utx = eth_inf.prepare_transaction(to_address=account2,
                                      from_address=account,
                                      nonce=nonce,
                                      gas=100001,
                                      value=value)
    (stx, errcode, errmsg) = keystore.sign_transaction(account, utx)
    return stx   

def check_for_tx(tx_hash):
    tx_data = eth_inf.eth_getTransactionByHash(tx_hash)
    if tx_data and tx_data['blockNumber']: #  means it's published     
        return (tx_data['value'],tx_data['blockNumber'],tx_data['transactionIndex'] ) 
    else:
        return None    


def wait_for_txs(tx_list, timeout=120):
    '''
    '''
    now = time.time()
    end_time = now + timeout
    while now < end_time:
        print('Polling. {0} secs left...'.format(int(end_time - now)))
        found = []
        for hash in tx_list:
            data = check_for_tx(hash)
            if data:
                print('Found: {0} in block {1} at pos {2}'.format(data[0], data[1], data[2]))
                found.append(hash)
                
        for hash in found:
            tx_list.remove(hash)
            
        if len(tx_list) == 0:
            break
        
        time.sleep(4)
        now = time.time()    



nonce = eth_inf.eth_getTransactionCount(account, return_raw=False)
print("Correct Nonce: {0}".format(nonce))

stx1 = prep_n_sign_tx(nonce, 0x1111)
stx2 = prep_n_sign_tx(nonce+1, 0x2222)
stx3 = prep_n_sign_tx(nonce+2, 0x3332)

hash2 = eth_inf.eth_sendRawTransaction(stx2)
print("Sent TX: {0}".format(hash2))
hash3 = eth_inf.eth_sendRawTransaction(stx3)
print("Sent TX: {0}".format(hash3))

wait_for_txs([hash2, hash3], 30)

hash1 = eth_rop.eth_sendRawTransaction(stx1)
print("Sent TX: {0}".format(hash1))

wait_for_txs([hash1, hash2, hash3], 120)



