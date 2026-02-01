from setuptools import setup, find_packages

setup(
    name="seisclass",
    version="0.1.5",
    author="Jia Luozhao",
    author_email="18429320@qq.com",
    description="Seismic event classification package",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/seisclass",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        "numpy>=1.19.0",
        "obspy>=1.2.0",
        "tensorflow>=2.0.0",
        "keras>=2.3.0",
        "joblib>=1.0.0",
        "scikit-learn>=0.24.0",
        "pandas>=1.1.0"
    ],
    package_data={
        'seisclass': ['model/251111nw/*', 'resource/*'],
    },
)
