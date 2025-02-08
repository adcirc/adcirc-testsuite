#!/usr/bin/env python3
"""
Script to package the test cases for use in the CircleCI environment

Written By: Zach Cobell
"""

def get_test_info(yaml_file: str) -> dict:
    """
    Get the list of tests to be packaged from the yaml file

    Args:
        yaml_file (str): The path to the yaml file containing the tests

    Returns:
        dict: A dictionary containing the tests to be packaged
    """
    import yaml
    with open(yaml_file, 'r') as f:
        tests = yaml.safe_load(f)
    return tests


def standard_files() -> list:
    """
    Get the list of standard files to include in all test tarballs

    Returns:
        list: A list of file paths to include in the tarball
    """
    return [
        "test_list.yaml",
        "RunSingleTest.sh",
        "test_runner/test_runner.py",
        "test_runner/adcirc_test/__init__.py",
        "test_runner/adcirc_test/adcirctest.py",
    ]


def check_semver(version: str) -> bool:
    """
    Check if the user provided version is a valid semantic version

    Args:
        version (str): The version to check

    Returns:
        bool: True if the version is a valid semantic version, False otherwise
    """
    import re
    semver = re.compile(r"^\d+\.\d+\.\d+$")

    # Remove the leading "v" if it exists
    if version[0] == "v":
        version = version[1:]

    return semver.match(version) is not None


def package_adcirc_tests():
    """
    Package the ADCIRC tests for upload to S3
    """
    import os
    import tarfile
    import argparse
    import boto3

    # Get the cli options
    parser = argparse.ArgumentParser(description="Package ADCIRC tests for S3")
    parser.add_argument("--yaml", help="The yaml file containing the tests to package (default: test_list.yaml)",
                        default="test_list.yaml")
    parser.add_argument("--version", type=str, help="The semantic version of the tests to package (i.e. v56.0.1)",
                        required=True)
    parser.add_argument("--upload", action="store_true", help="Upload the tarballs to S3 (default: false)",
                        default=False)
    parser.add_argument("--bucket", type=str,
                        help="The S3 bucket to upload the tarballs to (default: adcirc-testsuite)",
                        default="adcirc-testsuite")
    parser.add_argument("--prefix", type=str, help="The prefix to use when uploading the tarballs (default: adcirc)",
                        default="adcirc")

    args = parser.parse_args()

    test_info = get_test_info(args.yaml)
    version = args.version
    if not check_semver(version):
        print("Invalid version provided. Must be in the format of 'x.y.z'")
        return

    # Make a directory to store the tarballs
    output_directory = "tarballs"
    os.makedirs(output_directory, exist_ok=True)

    # If we are uploading, create the boto client here
    if args.upload:
        s3 = boto3.client("s3")
    else:
        s3 = None

    # Make sure the directory is empty
    for file in os.listdir(output_directory):
        print(f"Removing {file}...")
        os.remove(os.path.join(output_directory, file))

    for test_index, test_name in enumerate(test_info["tests"].keys()):
        print(f"Packaging [{test_index + 1}/{len(test_info['tests'])}]: {test_name}")
        test_path = test_info["tests"][test_name]["path"]
        output_name = os.path.join(output_directory, f"{test_name}.tar.gz")

        # Create a tarball of the test and the standard files
        with tarfile.open(output_name, "w:gz") as tar:
            for file in standard_files():
                tar.add(file)
            tar.add(test_path, arcname=test_path)

        # Push the test up to s3
        if args.upload:
            print(f"   Uploading '{output_name}' to S3 as "
                  f"'s3://{args.bucket}/{args.prefix}/{version}/{os.path.basename(output_name)}'")
            s3.upload_file(output_name, args.bucket, f"{args.prefix}/{version}/{os.path.basename(output_name)}")
            os.remove(output_name)

    # When we are done, if we were not uploading, we can remove the tarballs directory
    if not args.upload:
        os.rmdir(output_directory)


if __name__ == "__main__":
    package_adcirc_tests()

