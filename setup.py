from setuptools import setup, Extension, find_packages
import sys, os

# The following line is modified by setver.bash
version = '1.6.1'

packages=[ # or better called "modules"
    'valkka',
    'valkka.multiprocess'
]

this_folder = os.path.dirname(os.path.realpath(__file__))
path = this_folder + '/requirements.txt'
install_requires = []
if os.path.isfile(path):
    with open(path) as f:
        install_requires = f.read().splitlines()

setup(
    name = "valkka-multiprocess",
    version = version,
    install_requires = install_requires,
    include_package_data=True,
    packages = packages,
    
    # metadata for upload to PyPI
    author           = "Sampsa Riikonen",
    author_email     = "sampsa.riikonen@iki.fi",
    description      = "Valkka multiprocessing classes as separate package",
    license          = "MIT",
    keywords         = "valkka multiprocessing",
    url              = "https://elsampsa.github.io/valkka-multiprocess/", # project homepage
    
    long_description ="""
    Valkka multiprocessing classes as separate package
    """,
    long_description_content_type='text/plain',
    classifiers      =[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Operating System :: POSIX :: Linux',
        # https://autopilot-docs.readthedocs.io/en/latest/license_list.html
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3'
    ]
)
