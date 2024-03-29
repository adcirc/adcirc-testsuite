import logging

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s :: %(levelname)s :: %(filename)s :: %(funcName)s :: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%Z",
)


def adcirc_testsuite_runner():
    """
    Main entrypoint for running the ADCIRC test suite
    """
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
    parser.add_argument("--test", type=str, help="Test name", required=False)
    parser.add_argument("--test-yaml", type=str, help="Test yaml file", required=True)
    parser.add_argument(
        "--test-root", type=str, help="Root directory for tests", required=True
    )
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument(
        "--continue-on-failure", action="store_true", help="Continue on failure"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    if not args.all and not args.test:
        msg = "Either --all or --test must be specified"
        raise ValueError(msg)

    if not os.path.exists(args.bin):
        msg = f"ADCIRC binary directory {args.bin} does not exist"
        raise FileNotFoundError(msg)

    all_test_info = yaml.safe_load(open(args.test_yaml))

    test_list = []
    if args.all:
        test_list = all_test_info["tests"]
    else:
        if args.test not in all_test_info["tests"]:
            msg = f"Test {args.test} not found in {args.test_yaml}"
            raise ValueError(msg)
        test_list.append(args.test)

    any_failure = False
    for i, test_name in enumerate(test_list):

        if len(test_list) > 1:
            logger.info(f"Running test {i+1} of {len(test_list)}: {test_name}")
        else:
            logger.info(f"Running test: {test_name}")

        test_data = all_test_info["tests"][test_name]
        this_test = AdcircTest(
            test_name, test_data, args.bin, args.test_root, args.tolerance, args.verbose
        )

        this_test.clean()
        status = this_test.run()
        this_test.plot(status)
        if not status["overall"]["passed"]:
            any_failure = True
            msg = f"Test {test_name} failed"
            if not args.continue_on_failure:
                raise ValueError(msg)
            else:
                logger.error(msg)

    if any_failure:
        raise ValueError("One or more tests failed")


if __name__ == "__main__":
    adcirc_testsuite_runner()
