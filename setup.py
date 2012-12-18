from setuptools import setup, find_packages
import subprocess

def get_long_desc():
    """Use Pandoc to convert the readme to ReST for the PyPI."""
    try:
        return subprocess.check_output(['pandoc', '-f', 'markdown', '-t', 'rst', 'README.mdown'])
    except:
        print "WARNING: The long readme wasn't converted properly"

setup(name='django-backup',
    version='0.1dev',
    description='A backup tool with local folder and Amazon Glacier support',
    long_description=get_long_desc(),
    author='Adam Brenecki',
    author_email='adam@brenecki.id.au',
    url='https://github.com/adambrenecki/django-icybackup',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'boto',
    ],
)
