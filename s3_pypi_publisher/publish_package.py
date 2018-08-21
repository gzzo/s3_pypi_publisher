import argparse
import base64
import binascii
import hashlib
import subprocess
import os

import boto3
import botocore.exceptions

from jinja2 import Environment, PackageLoader


class PackageExists(Exception):
    pass


def get_package_name():
    # We assume that the package name is the same as the folder name
    return os.path.basename(os.getcwd())


def build_distributions():
    cmd = ['/usr/bin/env', 'python', 'setup.py', 'bdist_wheel', 'sdist']

    subprocess.check_call(cmd)

    walk = list(os.walk('dist'))
    return sorted(
        (os.path.join(walk[0][0], file) for file in walk[0][2]),
        key=os.path.getctime)[-2:]


def calculate_distribution_md5_base64(wheel):
    hash_md5 = hashlib.md5(open(wheel, 'rb').read())
    return base64.b64encode(hash_md5.digest()).decode('utf-8')


def upload_distributions(bucket, distributions, override=True):
    s3 = boto3.client('s3')

    for distribution in distributions:

        key = '{}/{}'.format(get_package_name(), os.path.basename(distribution))

        if not override:
            try:
                s3.head_object(Bucket=bucket, Key=key)
            except botocore.exceptions.ClientError as err:
                if err.response['Error']['Code'] != '404':
                    raise err
            else:
                raise PackageExists()

        distribution_md5 = calculate_distribution_md5_base64(distribution)
        s3.put_object(
            Body=open(distribution, 'rb'),
            Bucket=bucket,
            Key=key,
            ContentMD5=distribution_md5,
            Metadata={
                'md5': distribution_md5
            }
        )


def upload_index(bucket):
    s3 = boto3.client('s3')
    objects = s3.list_objects(Bucket=bucket, Prefix=get_package_name() + '/')['Contents']

    wheels = []
    for key in objects:
        if 'index.html' in key['Key']:
            continue
        metadata = s3.head_object(Bucket=bucket, Key=key['Key'])
        md5 = None
        if metadata['Metadata'].get('md5'):
            md5 = binascii.hexlify(base64.b64decode(metadata['Metadata']['md5'])).decode('utf-8')
        distribution_name = os.path.basename(key['Key'])
        url = distribution_name
        if md5:
            url = '{}#md5={}'.format(distribution_name, md5)

        wheels.append(dict(
            name=distribution_name,
            url=url
        ))

    template = Environment(loader=PackageLoader('s3_pypi_publisher')).get_template('index.html.j2')

    render = template.render({'wheels': wheels, 'name': get_package_name()})

    s3.put_object(
        Body=render,
        Bucket=bucket,
        Key='{}/index.html'.format(get_package_name()),
        ContentType='text/html',
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('bucket')
    args = ap.parse_args()

    distributions = build_distributions()
    upload_distributions(args.bucket, distributions)
    upload_index(args.bucket)


if __name__ == "__main__":
    main()
