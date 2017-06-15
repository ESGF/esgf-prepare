#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(name='esgprep',
      version='2.7.5',
      description='Toolbox to prepare data for ESGF publication',
      author='Levavasseur Guillaume',
      author_email='glipsl@ipsl.fr',
      url='https://github.com/IS-ENES-Data/esgf-prepare',
      packages=find_packages(),
      include_package_data=True,
      install_requires=['lockfile==0.12.2',
                        'requests==2.17.3',
                        'github3.py==0.9.5',
                        'uritemplate.py==2.0.0',
                        'fuzzywuzzy==0.15.0',
                        'netCDF4==1.2.8',
                        'hurry.filesize==0.9',
                        'treelib==1.3.5',
                        'tqdm==4.11.2'],
      platforms=['Unix'],
      zip_safe=False,
      entry_points={'console_scripts': ['esgprep=esgprep.esgprep:run']},
      classifiers=['Development Status :: 5 - Production/Stable',
                   'Environment :: Console',
                   'Intended Audience :: Science/Research',
                   'Intended Audience :: System Administrators',
                   'Natural Language :: English',
                   'Operating System :: Unix',
                   'Programming Language :: Python :: 2.5',
                   'Topic :: Scientific/Engineering',
                   'Topic :: Software Development :: Build Tools']
      )
