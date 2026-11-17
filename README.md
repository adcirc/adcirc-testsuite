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

### Builds that are not expected to match
The control solutions are generated with the Intel compilers. Some builds, such as the gfortran build used to collect
code coverage, are not expected to match them. For those, `--allow-mismatch` runs the tests and reports any
differences from the control solutions as warnings instead of failures, and always runs both portions of a hotstart
test. A model that fails to run, or an output file that is missing, is still a failure. `--report <file>` writes the
comparison results for each test to a JSON file. With `RunSingleTest.sh`, arguments after the test name are passed to
the runner:
```
./RunSingleTest.sh <path/to/adcirc/build> <name_of_test> --allow-mismatch --report results.json
```

### Creating or regenerating control solutions
`--update-controls` runs the tests and copies each test's output files into its `control` directory instead of
comparing them. Use it with the Intel build to create the control solutions for a new case, or to regenerate them
after an intended change in the results:
```
./RunSingleTest.sh <path/to/adcirc/build> <name_of_test> --update-controls
```

### Test definitions
Each test in `test_list.yaml` lists the files compared against the control solution in `output_files`. A test can
also set:

- `hotstart_output_files`: files compared only for the hot-start portion of a hotstart test, such as harmonic analysis
  results when the analysis spans the hotstart.
- `expected_files`: files the run must write but that the runner cannot compare, such as XDMF output. The test fails
  if any of them is missing or empty.
- `preprocess`: programs from the ADCIRC build directory to run in the test directory before the model, to generate
  inputs. For example, to make the NWS = 20 `fort.22` from a track with `aswip`:
  ```yaml
  preprocess:
    - executable: aswip
      args: ["-w", "aswip_input.22"]
      rename:
        NWS_20_fort.22: fort.22
  rm_files:
    - fort.22
  ```
  `rename` moves the files a step wrote to the names the model reads, and generated files should be listed in
  `rm_files` so they are removed before each run.

## Submitting a new case
New cases are definitely welcomed. Anyone looking to submit a new case should follow one of the other directories as 
an example of how a case should be constructed. Cases should exercise a feature or combination of features that is 
not currently part of the test suite. Cases should be able to be run in under 5 minutes in serial to avoid the suite 
becoming too cumbersome to run. Cases should be submitted either to zcobell@thewaterinstitute.org or via Pull Request 
with a description of the case and what it aims to test.
