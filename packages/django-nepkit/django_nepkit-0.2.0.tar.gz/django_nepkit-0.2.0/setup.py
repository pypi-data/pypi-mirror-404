from setuptools import find_packages, setup

setup(
    name="django-nepkit",
    version="0.2.0",
    include_package_data=True,
    author="Sankalp Tharu",
    author_email="sankalptharu50028@gmail.com",
    description="Django Nepali date, time, datetime, phone, and address fields with helpers.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/S4NKALP/django-nepkit",
    classifiers=[
        "Framework :: Django",
        "Framework :: Django :: 4.2",
        "Framework :: Django :: 5.0",
        "Framework :: Django :: 6.0",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
        "Operating System :: OS Independent",
        "Natural Language :: English",
    ],
    python_requires=">=3.11",
    packages=find_packages(exclude=("tests*",)),
    install_requires=[
        "django>=4.2,<6.0",
        "nepali>=1.1.3",
    ],
    extras_require={
        "drf": ["djangorestframework>=3.14"],
    },
)
