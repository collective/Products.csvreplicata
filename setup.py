from setuptools import setup, find_packages
import os
import sys

version = '1.1.11'

setupdir = os.path.abspath(
    os.path.dirname(__file__)
)

def read(*rnames):
    return open(
        os.path.join(setupdir, *rnames)
    ).read()

long_description = '%s' % (
    read('README.rst')          + '\n' +
    read('docs', 'INSTALL.txt') + '\n' +
    'Detailled documentation'   + '\n' +
    '======================='   + '\n' +
    read('Products', 'csvreplicata', 'tests', 'csvreplicata.txt') + '\n' +
    read('Products', 'csvreplicata', 'tests', 'exportimport.txt') + '\n' +
    read('Products', 'csvreplicata', 'tests', 'handlers.txt') + '\n' +
    read('Products', 'csvreplicata', 'tests', 'download.txt') + '\n' +
    read('docs', 'HISTORY.txt') + '\n' +
    ''
)

if 'RST_TEST' in os.environ:
    print long_description
    sys.exit(1)

setup(name='Products.csvreplicata',
      version=version,
      description="CSV import/export for Archetypes or other contents (via plugins for the later). Created by Makina Corpus.",
      long_description=long_description,
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='archetypes, import/export, csv, replication, synchronisation',
      author='Eric BREHAULT',
      author_email='eric.brehault@makina-corpus.org',
      url='https://svn.plone.org/svn/collective/Products.csvreplicata',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['Products'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'Products.AdvancedQuery >= 3.0.3' ,
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
