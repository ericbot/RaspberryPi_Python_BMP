from ez_setup import use_setuptools
use_setuptools()
from setuptools import setup, find_packages


setup(name              = 'Python_BMP',
      version           = '1.0.0',
      description       = 'Python library for accessing the BMP180 sensor',
      license           = 'Public Domain',
      url               = 'https://github.com/ericbot/RaspberryPi_Python_BMP/',
      dependency_links  = ['http://github.com/ericbot/RaspberryPi_Python_I2C/tarball/master#egg=Python-I2C-1.0.0'],
      packages          = find_packages())
