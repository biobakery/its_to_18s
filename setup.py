from setuptools import setup, find_packages

setup(
    name='its_to_18s',
    version='0.0.1',
    description="Convert taxonomy calls to 18s sequences",
    zip_safe=False,
    classifiers=[
        "Development Status :: 1 - Pre-Alpha"
    ],
    packages=['its_to_18s'],
    install_requires=[
        "leveldb==0.193"
    ],
    entry_points={
        'console_scripts': [
            'its_to_18s = its_to_18s.cli:main'
        ]
    },
    package_data={
        'its_to_18s' : [
            'indexes/*',
        ]
    }
)
