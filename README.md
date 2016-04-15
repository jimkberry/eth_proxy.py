
## eth_proxy ##

(Thanks for the help everyone)

This is an ethereum proxy to make it easier for me to do the things I want to do - and hide
some of the complexities involved.

Also, and maybe more importantly, it provides the capability to synchronously do things (create a contract, 
send a transaction) and then wait until they are in place.

In addition, it provides delegate-based asyncronous interaction with ethereum contracts via the EthContract class.


### Installing ###

Nothing really to install, except for dependencies. To install them:

- setup a virtualenv if you wish
- `pip install -r requirements-bast.txt`

If you want to implement an Ethereum account keystore (probably not really part of an
Ethereum proxy layer, but I need it on occasion) then you need to also:
- `pip install -r requirements-bast.txt`  

### Running the test scripts ###

- Make sure there is an ethereum node running and providing net services via rpc 

???

let me know if you find anything or have any ideas.

-jim


