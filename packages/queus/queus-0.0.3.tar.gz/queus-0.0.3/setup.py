from setuptools import setup, find_packages
from Queue import DATA01, DATA02, DATA03
from Queue import pythons, appname
from Queue import mention, profile
from Queue import version, clinton

with open("README.md", "r") as mess:
    description = mess.read()

setup(name=appname,
      url=profile,
      author=clinton,
      version=version,
      keywords=mention,
      description=DATA03,
      classifiers=DATA02,
      author_email=DATA01,
      python_requires=pythons,
      packages=find_packages(),
      long_description=description,
      long_description_content_type="text/markdown")
