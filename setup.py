from setuptools import setup


setup(
    name='wideq',
    version='0.0.0',
    description='LG SmartThinQ API client',
    author='Adrian Sampson',
    author_email='adrian@radbox.org',
    url='https://github.com/sampsyo/wideq',
    license='MIT',
    platforms='ALL',
    install_requires=['requests'],
    py_modules=['wideq'],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
)
