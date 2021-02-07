from distutils.core import setup

setup(
    name="cftool",
    version="1.0.0",
    description="cftools is a wrapper cli for 'aws cloudformation'",
    author="Ville M. Vainio",
    author_email="ville.vainio@basware.com",
    url="https://github.com/vivainio/cftool",
    packages=["cftool"],
    install_requires=["argp", "pydantic"],
    entry_points={"console_scripts": ["cftool = cftool.cli:main"]},
)
