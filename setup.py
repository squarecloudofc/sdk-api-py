from setuptools import setup

setup(name='squarecloud-api',
    version='0.0.1',
    license='MIT License',
    author='Robert Nogueira',
    long_description='Wrapper não oficial da SquareCloud API',
    long_description_content_type="text/markdown",
    author_email='robertlucasnogueira@gmail.com',
    keywords='squarecloud api python',
    description=u'Wrapper não oficial da SquareCloud API',
    packages=['squarecloud'],
    install_requires=['aiohttp~=3.8.3'],)