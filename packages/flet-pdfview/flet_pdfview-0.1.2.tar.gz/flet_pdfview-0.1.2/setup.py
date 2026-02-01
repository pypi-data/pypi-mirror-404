from setuptools import setup , find_packages
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()
    setup(
        name="flet_pdfview",
        description="Flet pdf view for all platforms",
        long_description=long_description,
        long_description_content_type="text/markdown",
        author="Mostafa Kessassi",
        author_email="mustaphakessassi76@gmail.com",
        version="0.1.2",
        python_requires=">=3.10",
        packages=find_packages(),
        install_requires=[
            "asyncio",
            "flet<=0.80.5",
            "pymupdf"
        ]
    )