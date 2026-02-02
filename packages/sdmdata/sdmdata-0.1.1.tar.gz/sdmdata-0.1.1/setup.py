from setuptools import setup, find_packages

setup(
    name='sdmdata',
    version='0.1.1',
    description='A library for Species Distribution Modeling data retrieval from GBIF, iNaturalist, and SpeciesLink APIs.',
    long_description=open('USAGE.md').read(),
    long_description_content_type='text/markdown',
    author='Ane Simões',
    author_email='anes.2017@alunos.utfpr.edu.br',
    packages=find_packages(),
    install_requires=[
        "pytest",
        "pandas",
        "requests",
        "python-dotenv",
        "pygbif",
        "pyinaturalist"
    ],
    license='MIT',
    python_requires='>=3.7',
)