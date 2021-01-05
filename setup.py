from setuptools import setup

setup(name='azulbot',
      version='0.1.0',
      description='Simulator and bot for the Azul game.',
      license='MIT',
      author='gleb-t',
      url='https://github.com/gleb-t/AzulBot',

      packages=['azulbot'],
      zip_safe=True, install_requires=['numpy'],
      classifiers=[
            'Development Status :: 4 - Beta',
            'Intended Audience :: Developers',
            'Topic :: Software Development :: Libraries',
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
      ],
)
