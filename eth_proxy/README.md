
## eth_proxy ##

(Thanks for the help everyone)

This is an ethereum proxy (currently using ethjsonrpc) to make it easier for me to do the things I want to do - and hide
some of the complexities involved.

Also, and maybe more importantly, it provides the capability to synchronously do things (create a contract, 
send a transaction) and then wait until they are in place.

In addition, it provides delegate-based asyncronous interaction with ethereum contracts via the EthContract class.


### Installing ###

Nothing really to install, except for dependencies. To install them:

- setup a virtualenv if you wish
- cd into the jsonrpc_wrap directory
- `pip install -r test_requirements.txt`

### Running the test script ###

- Make sure there is an ethereum node running and providing net services via rpc and with an unlocked account
- Edit 'jrw_test.py':
  - to point to the ethereum node (rpc_host and rpc_port)
  - to pecify the unlocked account (account)
- `python jrw_test.py`

let me know if you find anything or have any ideas.

-jim


