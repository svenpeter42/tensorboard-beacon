from setuptools import setup

setup(
    name='beacon',
    packages=['beacon'],
    include_package_data=True,
    entry_points={
        'console_scripts': ['beacon=beacon:main'],
    },
)
