from distutils.core import setup
setup(
  name = 'BoilingData', 
  packages = ['BOILINGDATA'],  
  version = '0.1.1',  
  license='MIT',
  description = 'BoilingData Python SDK',
  author = 'BoilingData', 
  author_email = 'info@boilingdata.com',
  url = 'https://github.com/boilingdata/python-boilingdata',
  download_url = 'https://github.com/user/reponame/archive/v_01.tar.gz',    # I explain this later on
  keywords = ['BoilingData', 'sql'], 
  install_requires=[
          'boto3',
          'botocore',
          'warrant',
          'websockets'
      ],
  classifiers=[
    'Development Status :: 4 - Beta" or "5',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
    'Intended Audience :: Developers',
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
  ],
)