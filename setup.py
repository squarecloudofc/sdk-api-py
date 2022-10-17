from setuptools import setup

setup(name='squarecloud-api',
    version='0.0.5',
    license='MIT License',
    author='Robert Nogueira',
    long_description='SquareCloud API wrapper',
    long_description_content_type="text/markdown",
    author_email='robertlucasnogueira@gmail.com',
    keywords='squarecloud api python',
    description=u'SquareCloud API wrapper',
    packages=['squarecloud'],
    install_requires=['aiohttp~=3.8.3'],)