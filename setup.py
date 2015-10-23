from setuptools import setup, find_packages

setup(name='esgmapfiles',
      version='0.6',
      description='Build ESGF mapfiles without esgscan_directory upon local ESGF datanode.',
      author='Levavasseur Guillaume',
      author_email='glipsl@ipsl.jussieu.fr',
      url='https://github.com/Prodiguer/esgf-mapfiles',
      packages=find_packages(),
      include_package_data=True,
      install_requires=['lockfile>=0.10.2'],
      plateforms=['Unix'],
      entry_points={'console_scripts': ['esgscan_directory=esgmapfiles.esgmapfiles:run', 'esg_mapfiles_check_vocab=esgmapfiles.checkvocab:main']},
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
