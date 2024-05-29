# ADCIRC Model Test Suite
The included suite of tests has been developed to test changes to the ADCIRC model and ensure solutions are consistent across releases. This suite is run any time a change is made to the model code and must pass before the code is allowed to be integrated into the upstream repository.

These also encompass a nice set of examples for users to get acquainted with setting up and running the model.

## Running the Suite
### Compiling for the suite
The automated test scripts may require the following ADCIRC executables to be compiled:
  1. adcirc
  2. padcirc
  3. adcswan
  4. padcswan
  5. adcprep

Depending on the modules used within the test suite, you may not need to compile all of these, 
though some tests may require certain features are enabled, such as netCDF or GRIB2 support.

### Running Tests
The test suite uses a python test apparatus. This runner relies on a yaml file to define the testing metadata.
The default test list is `test_list.yaml` and is located in the root directory fo this repository. It is possible
to leverage your own tests by modifying this file or creating a new one. The test suite produces a series of plots
as well to aid diagnosing any issues that may arise.

To run the full set of tests, the following command is used:
```
python3 test_runner/test_runner.py --all --bin <path/to/adcirc/build> --test-yaml test_list.yaml --tolerance 0.00001 --test-root .
```

You can also run a single test by specifying the test name:
```
python3 test_runner/test_runner.py --test <name_of_test> --bin <path/to/adcirc/build> --test-yaml test_list.yaml --tolerance 0.00001 --test-root .
```

Note that the default testing tolerance is 0.00001. This can be adjusted by changing the `--tolerance` flag. It may be
useful to do so depending on your build settings and compiler. 

## Submitting a new case
New cases are definitely welcomed. Anyone looking to submit a new case should follow one of the other directories as 
an example of how a case should be constructed. Cases should exercise a feature or combination of features that is 
not currently part of the test suite. Cases should be able to be run in under 5 minutes in serial to avoid the suite 
becoming too cumbersome to run. Cases should be submitted either to zcobell@thewaterinstitute.org or via Pull Request 
with a description of the case and what it aims to test.
