from setuptools import setup, find_packages

setup(
    name='credstash-local',
    version='1.0.0',
    description='A utility for managing secrets in using AWS KMS',
    license='Apache2',
    url='https://github.com/hirenj/credstash-local',
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        ],
    install_requires=['boto>=2.38.0', 'pycrypto>=2.6.1', 'boto3>=1.1.1'],
    extras_require = {'YAML': ['PyYAML>=3.10']},
    scripts=['credstash-local.py'],
    py_modules=['credstash-local'],
    entry_points={
        'console_scripts': [
            'credstash-local = credstash-local:main'
            ]
        }
    )
