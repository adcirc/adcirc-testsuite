import logging

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s :: %(levelname)s :: %(filename)s :: %(funcName)s :: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%Z",
)


def adcirc_testsuite_runner():
    import argparse
    import yaml
    import os
    from adcirc_test.adcirctest import AdcircTest

    parser = argparse.ArgumentParser(description="ADCIRC Test Suite Runner")
    parser.add_argument(
        "--bin", type=str, help="Path to the ADCIRC binary directory", required=True
    )
    parser.add_argument(
        "--tolerance", type=float, help="Tolerance for the test results", required=True
    )
    parser.add_argument("--test", type=str, help="Test name", required=True)
    parser.add_argument("--test-yaml", type=str, help="Test yaml file", required=True)
    parser.add_argument(
        "--test-root", type=str, help="Root directory for tests", required=True
    )

    args = parser.parse_args()

    if not os.path.exists(args.bin):
        msg = f"ADCIRC binary directory {args.bin} does not exist"
        raise FileNotFoundError(msg)

    all_test_info = yaml.safe_load(open(args.test_yaml))
    test_name = args.test
    if test_name not in all_test_info["tests"]:
        msg = f"Test {test_name} not found in {args.test_yaml}"
        raise ValueError(msg)

    test_data = all_test_info["tests"][test_name]
    this_test = AdcircTest(
        test_name, test_data, args.bin, args.test_root, args.tolerance
    )

    this_test.clean()
    passed = this_test.run()
    this_test.plot()
    if not passed:
        raise ValueError(f"Test {test_name} failed")


if __name__ == "__main__":
    adcirc_testsuite_runner()
