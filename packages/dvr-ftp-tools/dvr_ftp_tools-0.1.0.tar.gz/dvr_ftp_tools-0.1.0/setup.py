from setuptools import setup, find_packages

setup(
    name="ftp-handlers",
    version="1.0.0",
    packages=find_packages(),
    author="Edilson claudino da silva",
    description="A recursive FTP file explorer and downloader for DVR systems",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    python_requires=">=3.6",
)