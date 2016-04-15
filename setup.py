from setuptools import setup

setup(name='eth_proxy',
      version='0.1',
      description='Ethereum JSON-RPC Proxy',
      url='http://github.com/jimkberry/eth_proxy',
      author='jimkberry',
      author_email='jimkberry@gmail.com',
      license='',
      packages=['eth_proxy'],
      install_requires=[
          'requests',
          'pycryptodome',
          'rlp'
      ],      
      zip_safe=False)