from distutils.core import setup

setup(
    name="cfut",
    version="1.2.2",
    description="cfut is a wrapper cli for 'aws cloudformation'",
    author="Ville M. Vainio",
    author_email="ville.vainio@basware.com",
    url="https://github.com/vivainio/cfut",
    packages=["cfut"],
    install_requires=["argp", "pydantic"],
    entry_points={"console_scripts": ["cfut = cfut.cli:main"]},
)
