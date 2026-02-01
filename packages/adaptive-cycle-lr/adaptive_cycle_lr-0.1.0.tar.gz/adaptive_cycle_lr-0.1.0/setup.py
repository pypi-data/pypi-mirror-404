from setuptools import setup, find_packages

setup(
    name="adaptive-cycle-lr",
    version="0.1.0",
    description="Loss-aware learning rate scheduler for PyTorch",
    author="Your Name",
    author_email="your@email.com",
    url="https://github.com/yourusername/adaptive-cycle-lr",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        "torch>=1.9",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
