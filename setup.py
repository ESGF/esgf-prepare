from setuptools import setup, find_packages

setup(name='esgprep',
      version='2.4.4',
      description='Toolbox to prepare data for ESGF publication',
      author='Levavasseur Guillaume',
      author_email='glipsl@ipsl.jussieu.fr',
      url='https://github.com/IS-ENES-Data/esgf-prepare',
      packages=find_packages(),
      include_package_data=True,
      install_requires=['lockfile>=0.10.2', 'requests>=2.9.1'],
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
