from setuptools import setup
from setuptools.command.install import install
import os
import sys

class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        install.run(self)
        # Fix line endings after installation
        if sys.platform.startswith('linux') or sys.platform == 'darwin':
            import site
            # Find where ikali.py was installed
            for site_dir in site.getsitepackages() + [site.getusersitepackages()]:
                ikali_path = os.path.join(site_dir, 'ikali.py')
                if os.path.exists(ikali_path):
                    # Read and fix line endings
                    with open(ikali_path, 'rb') as f:
                        content = f.read()
                    # Replace CRLF with LF
                    content = content.replace(b'\r\n', b'\n')
                    with open(ikali_path, 'wb') as f:
                        f.write(content)
                    break

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ikali",
    version="v2.0.0",
    author="Hypa",
    author_email="hypertobayt@gmail.com",
    description="iKali, runs a command when typing ikali into the terminal.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/HypaTobaYT/ikali",
    py_modules=["ikali"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Environment :: Console",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "ikali=ikali:main",
        ],
    },
    cmdclass={
        'install': PostInstallCommand,
    },
)


