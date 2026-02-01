from setuptools import setup
import os

about = {}

here = os.path.abspath(os.path.dirname(__file__))
version_file = os.path.join(here, "brokenxapi", "__version__.py")

with open(version_file, encoding="utf-8") as f:
    exec(f.read(), about)

setup(
    version=about["__version__"],
    zip_safe=False,
)
