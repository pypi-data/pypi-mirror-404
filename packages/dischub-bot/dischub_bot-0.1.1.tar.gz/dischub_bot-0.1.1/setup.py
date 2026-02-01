from setuptools import setup, find_packages

setup(
    name="dischub_bot",  # PyPI name
    version="0.1.1",
    packages=find_packages(),
    include_package_data=True,  # include non-Python files
    package_data={
        # Include all templates and static files in the package
        "dischub_bot": [
            "templates/*.html",
            "templates/**/*.html",
            "static/*",
            "static/**/*",
        ],
    },
    install_requires=[
        "MetaTrader5",
        "requests",
        "django>=4.2",
    ],
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "launch-dischub=dischub_bot:launch_bot_ui",
        ],
    },
    author="DiscHub",
    author_email="chihoyistanford@gmail.com",
    description="Dischub automated scalping bot for MetaTrader 5",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://dischub.co.zw",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: Microsoft :: Windows",
        "License :: OSI Approved :: MIT License",
    ],
)
