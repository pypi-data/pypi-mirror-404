from setuptools import setup, find_packages

setup(
    name="dizi",
    version="1.1",
    author="Dang Dizi",
    author_email="dangdizi.75@gmail.com",
    description="Dizi theme",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.7",
)
