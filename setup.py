from setuptools import setup, find_packages

install_requires = ['cffi>=1.5.2']

setup(
    name='pyVulkan',
    version='0.2',
    description='vulkan API bindings for Python',
    author='latte10am',
    author_email='latte10am@gmail.com',
    packages=find_packages(),
    package_data={'': ['*.h']},
    install_requires=install_requires,
    url = 'http://pyopengl.sourceforge.net',
    license = 'BSD',
    keywords = 'Graphics,3D,Vulkan,cffi',
    classifiers = [
        """License :: OSI Approved :: BSD License""",
        """Programming Language :: Python""",
        """Topic :: Multimedia :: Graphics :: 3D Rendering""",
        """Topic :: Software Development :: Libraries :: Python Modules""",
        """Intended Audience :: Developers""",
    ],
    )