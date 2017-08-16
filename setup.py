from setuptools import setup

setup(name='belpy',
      version='1.0.0',
      description='BEL parsing and manipulation library',
      url='https://github.com/belbio/belpy',
      author='William Hayes, David Chen',
      author_email='',
      license='Apache',
      packages=['belpy'],
      include_package_data=True,
      install_requires=['click==6.7', 'TatSu==4.2.2', 'PyYAML==3.12'],
      entry_points={
        'console_scripts': [
            'bel=belpy.scripts:bel'
        ]
      },
      zip_safe=False)