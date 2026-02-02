# pylint: disable=import-error
from setuptools import setup, find_packages

setup(
    name='ipulse_shared_core_ftredge',
    version='27.9.1',  # Fix: Correct timestamp conversion for Firebase Auth (ms to datetime)
    package_dir={'': 'src'},  # Specify the source directory
    packages=find_packages(where='src'),  # Look for packages in 'src'
    install_requires=[
        # List your dependencies here
        'fastapi~=0.128.0',
        'pydantic[email]~=2.12.5',
        'python-dateutil~=2.9.0',
        'ipulse_shared_base_ftredge~=12.12.0',
    ],
    author='Russlan Ramdowar',
    description='Shared Core models and Logger util for the Pulse platform project. Using AI for financial advisory and investment management.',
    url='https://github.com/TheFutureEdge/ipulse_shared_core',

    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.12',
)