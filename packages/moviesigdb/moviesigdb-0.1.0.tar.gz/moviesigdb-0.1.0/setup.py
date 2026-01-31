from setuptools import setup, find_packages

setup(
    name="moviesigdb",
    version="0.1.0",
    description="A tool to generate movie barcodes and analyze video colors",
    
    # This tells Python to look inside the 'src' folder for your code
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    
    # Dependencies that will be installed automatically
    install_requires=[
        "numpy",
        "opencv-python",
        "matplotlib",
        "tqdm"
    ]
)