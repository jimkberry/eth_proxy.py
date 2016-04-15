# eth_proxy #

## Goals ##

The main goal is to provide a library that with as few dependencies as possible allows you to communicate with an Ethereum node using the JSON-RPC API.

Desired features:

- Minimize dependencies and external requirements
- Work as-is under Linux and Windows
- Provide a low-level API that implements all of the JSON-RPC commands in a "call 'em drectly" sort of way.
- Be useful for ad-hoc prototyping: developers should be able to write simple linear scripts that can provide end-to-end function: create a contract, wait for it to be mined, send it some data, etc - all in a single serial script.
- Provide a high-level delegate-based asynchronous API for applications. 
- Include an abstraction of an Ethrerum contract which can manage source code, ABI definitions and all of that, and leave a developer with the ability to interact with a contract in a natural-seeming way.
- Have hooks of some sort to help deal with transaction signing in a "ready for prime time" way. Don't assume unlocked node-managed accounts (but do support them.)

## Layers ##

#### Low Level ####

Makes it seem that you are dealing directly with the Node itself. `Call eth_clocknumber()` and get a number back. Transactions and contracts are not super-easy this way, because the calling code is responsible for know about and handling the idea that you have to wait and check for results.

Implements all Ethereum JSON-RPC commands. Many of these commands take an optional named "return_raw" boolean (defaults to False) that if True tells EthProxy to return the actual hex string returned by the JSON command, rather than translating it into an appropriate native type.

Implements transactions unsing a 3-step *Prepare/Sign/Submit* abstraction. First you **prepare** a transaction by calling `prepareSimpleTransaction()`, `prepareContractCreationTx()`, or `prepareContractFunctionTx()` depending on what you are trying to do. 

These 3 methods "prepare" an unsigned  transaction. In other words, they take the parameters that go into the transaction (to, from, contract addr, function signature and params…), RLP encode them, and then return a hex string which represents the transaction and could be sent to `eth_sendRawTransaction()`. 

But it can't be sent to `eth_sendRawTransaction()` because it's not signed. The `EthProxy` class itself does not sign transactions because this will generally be delegated to some external actor. On the other hand, the library provides a `TranasctionSigner` interface which can be used to connect to a signer. It also provides (mostly as an example) a `LocalKeystore` class which implements TransactionSigner and can manage accounts locally, as well as a `NodeSigner` class which talsk to an ethereum node and signs transactions for accounts that the node manages.

After the transaction is signed (the result is another hex string representing an RLP-encoded transaction) it can be sent to `eth_sendRawTansaction()`

In addition, there is a `getTransactionLogs()` method which fetches log entries from the receipt for a particular tx hash. I do that a lot and wanted a shorthand way to do it.

An application will typically use some these low-level calls, but will normally use the high-level API. They are interoperable.

#### Mid-level Synchronous ####



#### High-level Asynchronous ####

#### Extras ####

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


