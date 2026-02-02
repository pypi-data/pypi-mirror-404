from setuptools import setup, find_packages

with open('C:\\Users\\DELL\\Desktop\\cfk\\0.0.0\\help\\help.md', 'r', encoding='utf-8') as f:
    long_description = f.read()
with open("README.md","r",encoding="utf-8") as d:
    long_description = long_description + d.read()

setup(
    name='PyToolsgr',
    version='0.0.1',
    description='A lightweight 2D/3D game engine based on Ursina',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='l-love-china',
    author_email='13709048021@163.com',
    url='https://github.com/l-love-china/PyToolsgr',
    packages=find_packages(),
    install_requires=[
        'ursina>=8.3.0'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.10',
        'Topic :: Games/Entertainment',
        'Topic :: Software Development :: Libraries :: pygame',
    ],
    python_requires='>=3.10',
    keywords='game engine 2d 3d ursina',
)