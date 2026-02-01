from setuptools import setup, find_packages

setup(
    name="hedayat_media",
    version="1.6.6",
    author="امیرحسین خزاعی",
    author_email="amirhossinpython03@gmail.com",
    description="یک کتابخانه جامع برای دسترسی به احادیث، قرآن، ذکر و اطلاعات جغرافیایی مساجد",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/amirhossinpython/hedayat_media",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "hedayat_media": ["data/*.json"],
    },
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "deep-translator>=1.8.1",
        "geopy>=2.3.0",
        "openai",
        "httpx",
        "beautifulsoup4"
        
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
