from setuptools import setup, find_packages

setup(
    name="m-you-tk",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "m_you": ["assets/*.ttf"],
    },
    install_requires=[
        "Pillow>=9.0.0",
    ],
)