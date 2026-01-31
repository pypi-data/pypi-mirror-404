"""
    seting up the package
"""
import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="basicprogressbar",
    version="1.1.1",
    author="Sumiza",
    author_email="sumiza@gmail.com",
    description="Basic progress bar and discord progress bar",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Sumiza/basicprogressbar/",
    project_urls={
        "Bug Tracker": "https://github.com/Sumiza/basicprogressbar/issues",
    },
    classifiers=[
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.10",
    extra_require = {
        "timer": ["secondstotext"],
        "discord": ["requests"],
        "async": ["httpx"],
        "all": ["secondstotext","requests","httpx"]
    }
)
