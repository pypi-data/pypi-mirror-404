import os

from setuptools import setup, find_packages

# Lire les dépendances depuis requirements.txt
# with open("./requirements.txt") as f: required = f.read().splitlines()

setup(name='querycraft',
      version='0.0.80',
      author='Emmanuel Desmontils',
      author_email='emmanuel.desmontils@univ-nantes.fr',
      maintainer='Emmanuel Desmontils',
      maintainer_email=' emmanuel.desmontils@univ-nantes.fr',
      keywords='SQL Step-By-Step Query Database',
      classifiers=['Topic :: Education', "Programming Language :: Python :: 3",
                   "Operating System :: OS Independent"],
      url='https://gitlab.univ-nantes.fr/ls2n-didactique/querycraft',
      packages=find_packages(),
      python_requires=">=3.11.0",
      install_requires=['argparse>=1.4.0', 'openai>=2.9.0', 'tincan>=1.0.0',
                        'mysql-connector-python>=9.0.0',
                        'ollama>=0.4.7', 'keyboard>=0.13.5',
                        'sqlglot==25.33.0','colorama>=0.4.6'],
      entry_points={'console_scripts': ['pgsql-sbs = querycraft.sqlsbs:pgsql',
                                        'sqlite-sbs = querycraft.sqlsbs:sqlite',
                                        'mysql-sbs = querycraft.sqlsbs:mysql',
                                        'sbs = querycraft.sqlsbs:main',
                                        'admin-sbs = querycraft.sqlsbs:admin',
                                        'exos-sbs = querycraft.sqlsbs:exos']},
      include_package_data=True,
      package_data={'querycraft': ['data/*','config/*','cookies/*','cache/*','templates/*','exos/*']},
      description='Provide usefully SQL classes and functions to execute SQL queries step by step',
      long_description=open(os.path.join(os.path.dirname(__file__), 'README.md')).read(),
      long_description_content_type="text/markdown",
      license='GPL V3',
      platforms='ALL',
      )
