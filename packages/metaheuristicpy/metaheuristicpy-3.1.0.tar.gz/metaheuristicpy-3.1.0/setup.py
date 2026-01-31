# setup.py
from setuptools import setup, find_packages
import os

# Function to read the README.md content


def read_readme():
    try:
        with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'README.md'), encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return ""


setup(
    name='metaheuristicpy',  # The name users will use to pip install
    version='3.1.0',  # current version 3.1.0
    # Automatically finds 'balipkg' and any sub-packages
    packages=find_packages(),

    # Crucial for including non-code files like models and data
    package_data={
        'metaheuristicpy': [
            # 'pretrained_models/characterner/CRF_1/*.pkl',
            # 'pretrained_models/characterner/CRF_2/*.pkl',
            # 'pretrained_models/characterner/SatuaNER/*.pkl',
            # 'pretrained_models/characterner/HMM/*.pkl',
            # 'pretrained_models/characterner/SVM/*.pkl',
        ],
    },
    include_package_data=True,  # Essential for using package_data

    install_requires=[
        'pandas==1.5.3',
        'numpy==1.24.2',
        'openpyxl==3.1.5',
        'matplotlib==3.6.3',
        'seaborn==0.11.1',
        'scipy==1.10.0',
        'scikit-learn==1.2.1'
    ],
    entry_points={
        # Optional: If you want to provide command-line scripts
        # 'console_scripts': [
        #     'analyze-balinese-text=balipkg.cli:main_function',
        # ],
    },

    author='I Made Satria Bimantara',
    author_email='satriabimantara.imd@gmail.com',
    description='A Python-based package of Metaheuristic Optimization Algorithms for Solving Continous and Discrete Optimization Problem',
    long_description=read_readme(),  # Reads content from README.md
    long_description_content_type='text/markdown',  # Specify content type for PyPI
    keywords=['Optimization', 'Metaheuristic', 'Swarm Intelligence',
              'Evolutionary Algorithm', 'Soft Computing'],
    classifiers=[
        # Or 4 - Beta, 5 - Production/Stable
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',  # Or your chosen license
        'Framework :: Jupyter',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Operating System :: OS Independent',
        'Natural Language :: Indonesian',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Scientific/Engineering :: Mathematics'
    ],
    python_requires='>=3.8',  # Minimum Python version
)
