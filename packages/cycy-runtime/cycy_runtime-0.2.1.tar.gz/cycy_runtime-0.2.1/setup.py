from setuptools import setup, find_packages
import os

def get_long_description():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, encoding='utf-8') as f:
            return f.read()
    return "CyCy：新一代Python全场景运行时，100%兼容CPython，全自动无感加速"

setup(
    name="cycy-runtime",
    version="0.2.1",
    author="蔡靖杰",
    author_email="1289270215@qq.com",
    description="CyCy：新一代Python全场景运行时",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=["Cython>=3.0.0","setuptools>=60.0.0"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.14',
        "Programming Language :: Python :: 3 :: Only",
        'Programming Language :: Python :: Implementation :: CPython',
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Interpreters",
    ],
    keywords="python runtime jit compiler",
    package_data={
        "cycy": ["*.py"],
    },
    include_package_data=True,
    cmdclass={},
)