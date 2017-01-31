from setuptools import setup
import platform

# signing is not needed if you use and external signer
signing_reqs = ['pbkdf2','bitcoin']

# scrypte is preferred, but usually a problem for windows:
# also c_secp256k1 is often a problem on any platform, or it ould be there too
if platform.system() != 'Windows':
    signing_reqs.append(['scrypt'])



setup(
    name='eth_proxy',
    version='0.1',
    description='Ethereum JSON-RPC Proxy',
    url='https://github.com/jimkberry/eth_proxy.py',
    author='jimkberry',
    author_email='jimkberry@gmail.com',
    license='',
    packages=['eth_proxy'],
    setup_requires =['pytest-runner',],
    tests_require=['pytest',],      
    install_requires=[
        'requests',
        'pycryptodome',
        'rlp',
    ],      
    extras_require={
      'signing': signing_reqs
    },
    zip_safe=False
)
