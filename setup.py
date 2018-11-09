#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from setuptools import setup, find_packages
from setuptools.command.install import install
from esgprep.utils.constants import VERSION


class InstallCommand(install):
    """
    Adds the --build-for-conda option to the install arguments

    """
    user_options = install.user_options + [
        ('build-for-conda', None, None),
    ]

    def initialize_options(self):
        install.initialize_options(self)
        self.build_for_conda = None

    def finalize_options(self):
        install.finalize_options(self)

    def run(self):
        install.run(self)


# run setup, but with conda handling all the dependencies
if '--build-for-conda' in sys.argv:
    setup(name='esgprep',
          cmdclass={'install': InstallCommand},
          version=VERSION,
          description='Toolbox to prepare data for ESGF publication',
          author='Levavasseur Guillaume',
          author_email='glipsl@ipsl.fr',
          url='https://github.com/ESGF/esgf-prepare',
          packages=find_packages(),
          include_package_data=True,
          platforms=['Unix'],
          zip_safe=False,
          entry_points={'console_scripts': ['esgmapfile=esgprep.esgmapfile:main',
                                            'esgdrs=esgprep.esgdrs:main',
                                            'esgfetchini=esgprep.esgfetchini:main',
                                            'esgfetchtables=esgprep.esgfetchtables:main',
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
# normal pip install process
else:
    setup(name='esgprep',
          cmdclass={'install': InstallCommand},
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
                            'requests==2.20.0',
                            'fuzzywuzzy==0.16.0',
                            'netCDF4==1.4.0',
                            'hurry.filesize==0.9',
                            'treelib==1.4.0'],
          platforms=['Unix'],
          zip_safe=False,
          entry_points={'console_scripts': ['esgmapfile=esgprep.esgmapfile:main',
                                            'esgdrs=esgprep.esgdrs:main',
                                            'esgfetchini=esgprep.esgfetchini:main',
                                            'esgfetchtables=esgprep.esgfetchtables:main',
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
