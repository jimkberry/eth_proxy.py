from setuptools import setup

signing_reqs = ['pbkdf2','bitcoin']

# preferred, but usually a problem for windows:
if platform.system() != 'Windows':
    signing_reqs.append(['scrypt','c_secp256k1'])



setup(
    name='eth_proxy',
    version='0.1',
    description='Ethereum JSON-RPC Proxy',
    url='http://github.com/jimkberry/eth_proxy',
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
