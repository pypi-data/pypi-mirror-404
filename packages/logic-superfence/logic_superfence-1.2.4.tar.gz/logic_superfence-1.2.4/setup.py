from setuptools import setup, find_packages

setup(
    name='logic_superfence',
    version='1.2.4',
    packages=find_packages(),
    include_package_data=True,
    author='Davy Cottet',
    description='A superfence pymarkdown extension to display Logic-Circuit-Simulator',
    url='https://logic-superfence.gitlab.io',
    license='GNU General Public License v3.0',
    platforms=['Any'],
    install_requires=[
          'markdown',
          'pymdown-extensions'
      ],
    entry_points={
        'mkdocs.plugins': [
            'logic = logic_superfence:LogicBundlePlugin'
        ]
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'
    ],
)


