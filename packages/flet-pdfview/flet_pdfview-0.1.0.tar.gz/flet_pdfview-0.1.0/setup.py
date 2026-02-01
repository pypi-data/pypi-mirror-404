from setuptools import setup , find_packages

setup(
    name="flet_pdfview",
    description="Flet pdf view for all platforms",
    long_description=open("README.md",mode="r").read(),
    long_description_content_type="text/markdown",
    author="Mostafa Kessassi",
    author_email="mustaphakessassi76@gmail.com",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "asyncio",
        "flet==0.80.2",
        "pymupdf",
    ]
)