from setuptools import setup, find_packages

setup(name='esgmapfiles',
      version='0.4',
      description='Build ESG-F mapfiles without esgscan_directory upon local ESG-F datanode.',
      author='Levavasseur Guillaume',
      author_email='glipsl@ipsl.jussieu.fr',
      url='http://esgf-mapfiles.readthedocs.org/en/latest/index.html',
      packages=find_packages(),
      install_requires=['lockfile>=0.10.2'],
      entry_points={'console_scripts': ['esg_mapfiles=esgmapfiles.esgmapfiles:main']}
      )
