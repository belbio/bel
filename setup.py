from setuptools import setup, find_packages

setup(
    name='bel_lang',
    version='1.0.0',
    description='BEL parsing and manipulation library',
    url='https://github.com/belbio/bel_lang',
    author='William Hayes, David Chen',
    author_email='',
    license='Apache',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        # Include all files in the bel_lang/versions directory
        'bel_lang': ['versions/*'],
    },
    install_requires=[
        'click==6.7',
        'TatSu==4.2.2',
        'PyYAML==3.12',
        'requests==2.18.4',
        'fastcache>=1.0.2',
    ],
    entry_points={
        'console_scripts': [
            'belstmt=bel_lang.scripts:bel',
        ]
    },
    zip_safe=False,
)
