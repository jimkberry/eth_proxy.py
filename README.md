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

## API Layers ##

#### Low Level ####

Makes it seem that you are dealing directly with the node itself. `Call eth_blockNumber()` and you get a number back. Working with transactions and contracts is not not super-easy this way.

Implements all (maybe) Ethereum JSON-RPC commands. Many of these commands take an optional boolean parameter named "return_raw" (defaults to False) that if True tells EthProxy to return the actual hex string returned by the JSON command, rather than translating it into an appropriate python type.

Transactions are handled using a 3-step *Prepare/Sign/Submit* abstraction. First you **prepare** a transaction by calling `prepareSimpleTransaction()`, `prepareContractCreationTx()`, or `prepareContractFunctionTx()` depending on what you are trying to do. These 3 methods take the parameters that go into the transaction (to, from, contract addr, function signature and params…), RLP encode them, and then return a hex string which represents the transaction and that could be sent to `eth_sendRawTransaction()`. 

But it can't be sent to `eth_sendRawTransaction()` because it's not signed. The `EthProxy` class itself does not sign transactions because this will generally be delegated to some external actor anyway. On the other hand, the library provides a `TranasctionSigner` interface which can be used to connect to a signer. It also provides (mostly as an example) a `LocalKeystore` class which implements TransactionSigner and manages accounts locally, as well as a `NodeSigner` class which talks to an ethereum node and has the node sign transactions for accounts that are managed by it (and unlocked).

After the transaction is signed it can be sent to `eth_sendRawTansaction()`

In addition, there is a `getTransactionLogs()` method which fetches log entries from the receipt for a particular tx hash. I do that a lot and wanted a shorthand way to do it.

An application will typically use some these low-level calls, but will normally use the high-level API. They are interoperable.

#### Mid-level Synchronous ####

This API is is mostly intended to allow developers to write simple scripts that can interact with transactions. The main feature of these methods is that they wait for transaction to be found in the current block before they return. Nothing real fancy - they just sleep/poll.

Functions at this level (and the high-level async as well) require that you call `attach_account( account_addr)` and `set_transaction_signer( EthereumTxSigner implementation)` after creating the `EthProxy` class.

Mid-level methods are `submit_transaction_sync()`, `install_compiled_contract_sync()` and `contract_function_tx_sync()` which first call the appropriate _prepare_ method for the type of transaction, then sign and submit it, and then wait for it to appear in the blockchain.

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


