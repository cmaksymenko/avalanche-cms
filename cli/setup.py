from setuptools import setup, find_packages

setup(
    name='avalanchecli',
    version='0.0.4',
    description='CLI for Avalanche CMS',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Christian Maksymenko',
    author_email='avalanchecms@cmaksymenko.com',
    url='https://github.com/cmaksymenko/avalanchecms/cli',
    license='Apache License 2.0',
    keywords="Avalanche, CMS, CLI, automation",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click', 'requests'
    ],
    python_requires=">=3.12, <4",
    entry_points={
        'console_scripts': [
            'av=av.cli:cli',
        ],
    },
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Utilities",
    ]
)