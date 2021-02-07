from distutils.core import setup

setup(
    name="cfut",
    version="1.0.0",
    description="cfut is a wrapper cli for 'aws cloudformation'",
    author="Ville M. Vainio",
    author_email="ville.vainio@basware.com",
    url="https://github.com/vivainio/cftool",
    packages=["cftool"],
    install_requires=["argp", "pydantic"],
    entry_points={"console_scripts": ["cfut = cftool.cli:main"]},
)
