from setuptools import setup

setup(
  name='sbdl',
  version='1.21.1',
  description = "System Behaviour Description Language (Compiler)",
  author = "Michael A. Hicks",
  author_email = "michael@mahicks.org",
  url = "https://sbdl.dev",
  py_modules=['sbdl','csv-to-sbdl','sbdl_server'],
  license = "Proprietary",
  python_requires='>=3.6',
  install_requires=['networkx','matplotlib','docx2txt','openpyxl','docxtpl','jinja2','pygls','lsprotocol'],
  entry_points={
    'console_scripts': [
      'sbdl = sbdl:run_main',
    ],
  }
)
