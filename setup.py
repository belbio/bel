from setuptools import setup

setup(
    name='bel_lang',
    version='1.0.0',
    description='BEL parsing and manipulation library',
    url='https://github.com/belbio/bel_lang',
    author='William Hayes, David Chen',
    author_email='',
    license='Apache',
    packages=['bel_lang'],
    include_package_data=True,
    install_requires=[
        'click==6.7',
        'TatSu==4.2.2',
        'PyYAML==3.12',
        'pytest==3.2.1',
        'requests==2.18.4',
    ],
    entry_points={
        'console_scripts': [
            'belstmt=bel_lang.scripts:bel',
        ]
    },
    zip_safe=False,
)
