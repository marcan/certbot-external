from setuptools import setup
from setuptools import find_packages

install_requires = [
    'acme',
    'certbot',
    'zope.interface',
]

setup(
    name='certbot-external',
    description="External hook plugin for Let's Encrypt client",
    url='https://github.com/marcan/certbot-external',
    author="Hector Martin",
    author_email='marcan@marcan.st',
    license='Apache License 2.0',
    install_requires=install_requires,
    packages=find_packages(),
    entry_points={
        'certbot.plugins': [
            'external = certbot_external.configurator:ExternalConfigurator',
        ],
    },
)
