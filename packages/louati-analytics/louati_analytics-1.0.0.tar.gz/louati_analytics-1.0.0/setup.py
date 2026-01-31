from setuptools import setup, find_packages

setup(
    name="louati_analytics",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'pandas',
        'numpy',
        'scipy',
        'tabulate',
        'plotly',
        'causalimpact',
        'fpdf',
        'qrcode',
        'pillow'
    ],
    author="Louati Mahdi",
    author_email="louatimahdi390@gmail.com",
    description="Powerful analytics library for querying, statistics, and visualization",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/mahdi123-tech/louati-analytics",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)