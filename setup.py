from setuptools import setup


def readme():
    with open('README.md') as readme_file:
        return readme_file.read()


def setup_package():
    setup(
        name='s3_pypi_publisher',

        version='0.1.0',

        description='A utility to publish Python packages to S3 buckets',

        long_description=readme(),

        author='Guido Rainuzzo',

        author_email='hi@guido.nyc',

        url='https://github.com/gzzo/s3_pypi_publisher',

        packages=['s3_pypi_publisher'],

        license='License :: OSI Approved :: Apache Software License 2.0 (Apache-2.0)',

        scripts=[
            'scripts/publish_package',
        ],

        install_requires=[
            'boto3',
            'jinja2'
        ]
    )


if __name__ == "__main__":
    setup_package()
