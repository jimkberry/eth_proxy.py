# eth_proxy #

---

## Goals ##

The main goal is to provide a library that with as few dependencies as possible allows you to communicate with an Ethereum node using the JSON-RPC API.

Desired features:

- Minimize dependencies and external requirements
- Work as-is under Linux and Windows
- Provide a low-level API that implements all of the JSON-RPC commands in a "call 'em drectly" sort of way.
- Be useful for ad-hoc prototyping: developers should be able to write simple linear scripts that can provide end-to-end function: create a contract, wait for it to be mined, send it some data, etc - all in a single serial script.
- Provide a delegate-based asynchronous API for applications. 
- Include an abstraction of an Ethrerum contract which can manage source code, ABI definitions and all of that, and leave a developer with the ability to interact wit a contract in a natural-seeming way.

---

## Layers ##

* Low Level *

* Mid-level Synchronous *

* High-level Asynchronous *

* Extras *

---

## Installing ##

Nothing really to install, except for dependencies. To install them:

`pip install -r requirements-base.txt`

If you want to implement an Ethereum account keystore (probably not really part of an
Ethereum proxy layer, but I need it on occasion) then you need to also:

`pip install -r requirements-sig.txt`  


### Running the test scripts ###

- Make sure there is an ethereum node running and providing net services via rpc 


let me know if you find anything or have any ideas.

-jim


