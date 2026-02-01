from setuptools import setup, find_packages

setup(
    name="Topsis-Prigya-102313061",   
    version="1.0.0",
    author="Prigya Goyal",
    author_email="goyalprigya@gmail.com",   
    description="Command line implementation of TOPSIS method",
    long_description=open("README.md").read(),   
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_prigya_102313061.topsis:main"
        ]
    },
    python_requires=">=3.6",   
)
