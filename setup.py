from setuptools import setup, find_packages

setup(name='esgmapfiles',
      version='1.1',
      description='Build ESGF mapfiles.',
      author='Levavasseur Guillaume',
      author_email='glipsl@ipsl.jussieu.fr',
      url='https://github.com/IS-ENES-Data/esgf-mapfiles',
      packages=find_packages(),
      include_package_data=True,
      install_requires=['lockfile>=0.10.2'],
      platforms=['Unix'],
      entry_points={'console_scripts': ['esgscan_directory=esgmapfiles.esgmapfiles:run', 'esgscan_check_vocab=esgmapfiles.checkvocab:main']},
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
