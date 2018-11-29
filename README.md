# ADCIRC Model Test Suite
The included suite of tests has been developed to test changes to the ADCIRC model and ensure solutions are consistent across releases. This suite is run any time a change is made to the model code and must pass before the code is allowed to be integrated into the upstream repository.

These also encompass a nice set of examples for users to get acquainted with setting up and running the model. 

## Included Cases
The following cases are included in the suite. Some tests are run in multiple ways to test different portions of the model code.


|Case| Model| Features| Description| Runs|
|----|-----|--------|-----------|----|
|adcirc-apes|ADCIRC|2D, NWS=3|5 day simulation using NWS=3 wind forcing in the Pamlico sound| Serial, Parallel|
|adcirc-internal-overflow|ADCIRC|2D, Weir boundaries, Tidal forcing| Example problem demonstrating weir overtopping| Serial, Parallel|
|adcirc-quarterannular-2d|ADCIRC|2D, Tidal forcing | Quarter Annular problem from Lynch and Gray (1979)|Serial, Parallel, netCDF, Parallel writer processors, Parallel netCDF writer processors|
|adcirc-shinnecock-inlet|ADCIRC|2D, Tidal forcing | Barrier island inlet example |Serial, Parallel|
adcirc-swan-apes-irene|ADCIRC+SWAN|2D, Wave forcing, SWAN coupling, NWS=320|Pamlico sound example with Hurricane Irene| Serial, Parallel|

## Running the Suite
### Compiling for the suite
The automated test script (```RunTests.sh```) requires the following executables are compiled with netCDF enabled:
  1. adcirc
  2. padcirc
  3. adcswan
  4. padcswan
  5. adcprep
  6. adcircResultsComparison (found in the util subdirectory of the ADCIRC source code)

### Running the Full Suite
To run the tests, the following command is used:
```
./RunTests.sh /path/to/adcirc/work/directory
```
Note that the path must be an absolute and not a relative path.

### Running a single case
If you are not conducting the full test of the code, you may want to run only a single test. In this case, each folder contains a ```run.sh``` file which executes the commands necessary to run the model. This file is run as:
```
./run.sh /path/to/adcirc/work/directory maxerr
```
In this case, relative paths may be used and you do not need to have all features turned on, only those required for a particular test. The ```maxerr``` parameter is set to ```err=0.00001``` in the main ```RunTests.sh``` script. 

## Submitting a new case
New cases are definitely welcomed. Anyone looking to submit a new case should follow one of the other directories as an example of how a case should be constructed. Cases should exercise a feature or combination of features that is not currently part of the test suite. Cases should be able to be run in under 10 minutes in serial to avoid the suite becoming too cumbersome to run. Cases should be submitted either to zachary.cobell@arcadis.com or via Pull Request with a description of the case and what it aims to test.
