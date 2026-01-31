from setuptools import setup, find_packages

setup(
    name='mobilizr-python',
    version='1.01',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'mobilizr_python.datasets': ['data/*.csv'],
    },
    install_requires=[
        'pandas',
    ],
    description='A library of custom datasets.',
    author='Emilio Dulay',
    author_email='emiliodulay19@g.ucla.edu',
    url="https://github.com/EmilioD19/mobilizr-python",
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
)
