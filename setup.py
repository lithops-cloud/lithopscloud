from setuptools import setup

setup(
   name='lithopscloud',
   version='1.0',
   description='A useful module',
   author='Pavel Kravchenko',
   author_email='kpavel@il.ibm.com',
   packages=['lithopscloud'],  #same as name
   install_requires=['ibm-cloud-sdk-core==3.10.0', 'ibm-platform-services==0.19.1', 'ibm-vpc==0.6.0'], #external packages as dependencies
)