#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from esgprep.utils.constants import VERSION

setup(name='esgprep',
      version=VERSION,
      description='Toolbox to prepare data for ESGF publication',
      author='Levavasseur Guillaume',
      author_email='glipsl@ipsl.fr',
      url='https://github.com/ESGF/esgf-prepare',
      packages=find_packages(),
      include_package_data=True,
      python_requires='>=2.7, <3.0',
      install_requires=['lockfile==0.12.2',
                        'esgconfigparser==0.1.17',
                        'requests==2.18.4',
                        'fuzzywuzzy==0.16.0',
                        'netCDF4==1.4.0',
                        'hurry.filesize==0.9',
                        'treelib==1.5.1',
                        'tqdm==4.23.4'],
      platforms=['Unix'],
      zip_safe=False,
      entry_points={'console_scripts': ['esgmapfile=esgprep.esgmapfile:run',
                                        'esgdrs=esgprep.esgdrs:run',
                                        'esgfetchini=esgprep.esgfetchini:run',
                                        'esgfetchtables=esgprep.esgfetchtables:run',
                                        'esgcheckvocab=esgprep.esgcheckvocab:run'
                                        ]},
      classifiers=['Development Status :: 5 - Production/Stable',
                   'Environment :: Console',
                   'Intended Audience :: Science/Research',
                   'Intended Audience :: System Administrators',
                   'Natural Language :: English',
                   'Operating System :: Unix',
                   'Programming Language :: Python',
                   'Topic :: Scientific/Engineering',
                   'Topic :: Software Development :: Build Tools']
      )
