from distutils.core import setup

setup(
    name="cfut",
    version="1.8.0",
    description="cfut is a wrapper cli for 'aws cloudformation', 'aws ecr' and some others",
    author="Ville M. Vainio",
    authr_email="ville.vainio@basware.com",
    url="https://github.com/vivainio/cfut",
    packages=["cfut"],
    install_requires=["argp", "pydantic", "PyYAML"],
    entry_points={"console_scripts": ["cfut = cfut.cli:main"]},
)
