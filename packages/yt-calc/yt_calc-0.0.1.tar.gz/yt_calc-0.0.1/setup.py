from setuptools import setup, find_packages
 
classifiers = [
  'Development Status :: 5 - Production/Stable',
  'Intended Audience :: Education',
  'Operating System :: OS Independent',
  'License :: OSI Approved :: MIT License',
  'Programming Language :: Python :: 3'
]
 
setup(
  name='yt_calc',
  version='0.0.1',
  description='Calculator that allows you to add, substract, multiply or divide 2 numbers.',
  long_description=open('README.txt').read() + '\n\n' + open('CHANGELOG.txt').read(),
  url='',  
  author='Dipansh Mahobia',
  author_email='mahobiadipansh@gmail.com',
  license='MIT', 
  classifiers=classifiers,
  keywords='calculator, basic calculator', 
  packages=find_packages(),
  install_requires=[''] 
)