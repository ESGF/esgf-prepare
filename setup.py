#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from esgprep.constants import VERSION


setup(name='esgprep',
      version=VERSION,
      description='Toolbox to prepare data for ESGF publication',
      author='Levavasseur Guillaume',
      author_email='glipsl@ipsl.fr',
      url='https://github.com/ESGF/esgf-prepare',
      packages=find_packages(),
      include_package_data=True,
      python_requires='<3.6',
      platforms=['Unix'],
      zip_safe=False,
      entry_points={'console_scripts': ['esgmapfile=esgprep.esgmapfile:main',
                                        'esgdrs=esgprep.esgdrs:main',
                                        'esgfetchini=esgprep.esgfetchini:main',
                                        'esgfetchtables=esgprep.esgfetchtables:main',
                                        'esgfetchcv=esgprep.esgfetchcv:main',
                                        'esgcheckvocab=esgprep.esgcheckvocab:main']},
      classifiers=['Development Status :: 5 - Production/Stable',
                   'Environment :: Console',
                   'Intended Audience :: Science/Research',
                   'Intended Audience :: System Administrators',
                   'Natural Language :: English',
                   'Operating System :: Unix',
                   'Programming Language :: Python',
                   'Topic :: Scientific/Engineering',
                   'Topic :: Software Development :: Build Tools'])
