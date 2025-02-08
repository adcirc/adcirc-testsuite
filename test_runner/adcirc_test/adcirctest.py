import logging
from typing import Tuple, Union, ClassVar

import numpy as np
import xarray as xr
from matplotlib.tri import Triangulation

logger = logging.getLogger(__name__)


class AdcircTest:
    """
    Class to run an ADCIRC test based on a test yaml file
    """

    # List of variables dropped to be read in by xarray
    ADCIRC_DROP_VARIABLES_LIST: ClassVar = [
        "neta",
        "nvel",
        "nvdll",
        "max_nvdll",
        "ibtype",
        "nbdv",
        "nvell",
        "nbvv",
        "ibtypee",
        "max_nvell",
    ]

    def __init__(
        self,
        test: str,
        test_yaml: dict,
        binary_directory: str,
        root_dir: str,
        tolerance: float,
        verbose: bool = False,
    ):
        """
        Initialize the AdcircTest object

        Args:
            test: Test name
            test_yaml: Test yaml dictionary
            binary_directory: Path to the ADCIRC binary directory
            root_dir: Root directory for the tests
            tolerance: Tolerance for the test results
            verbose: Verbose output
        """

        if verbose:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

        self.__bin = binary_directory
        self.__tolerance = tolerance
        self.__test = test
        self.__test_yaml = test_yaml
        self.__root_dir = root_dir
        self.__executable, self.__prep_executable = self.__find_executable()
        self.__test_directory = self.__find_test_directory()
        self.__is_global = self.__test_yaml.get("global", False)
        self.__is_geographic = self.__test_yaml.get("geographic", False)

        logger.debug(f"AdcircTest object created for test: {test}")
        logger.debug(f"Executable: {self.__executable}")
        logger.debug(f"Test directory: {self.__test_directory}")

    def __repr__(self):
        """
        String representation of the object

        Returns: String representation
        """
        return f"AdcircTest(bin={self.__bin}, tolerance={self.__tolerance}, test={self.__test}, test_yaml={self.__test_yaml})"

    def __find_executable(self) -> Tuple[str, str]:
        """
        Find the executable based on the test yaml file

        Returns:
            Tuple of (model executable, prep executable)
        """
        import os

        prep_executable = None
        model_executable = None

        if self.__test_yaml["model"] == "adcirc":
            logger.debug("Searching for ADCIRC executables")
            if self.__test_yaml["parallel"]:
                model_executable = os.path.join(self.__bin, "padcirc")
                prep_executable = os.path.join(self.__bin, "adcprep")
            else:
                model_executable = os.path.join(self.__bin, "adcirc")
        elif self.__test_yaml["model"] == "adcirc+swan":
            logger.debug("Searching for ADCIRC+SWAN executables")
            if self.__test_yaml["parallel"]:
                model_executable = os.path.join(self.__bin, "padcswan")
                prep_executable = os.path.join(self.__bin, "adcprep")
            else:
                model_executable = os.path.join(self.__bin, "adcswan")
        else:
            msg = f"Model {self.__test_yaml['model']} not supported"
            raise ValueError(msg)

        if not os.path.exists(model_executable):
            msg = f"Executable {model_executable} does not exist in {self.__bin}"
            raise FileNotFoundError(msg)

        if prep_executable and not os.path.exists(prep_executable):
            msg = f"Executable {prep_executable} does not exist in {self.__bin}"
            raise FileNotFoundError(msg)

        # Get the absolute path to the executable
        model_path = os.path.abspath(model_executable)
        prep_path = os.path.abspath(prep_executable) if prep_executable else None

        return model_path, prep_path

    def __find_test_directory(self) -> str:
        """
        Find the test directory based on the test yaml file

        Returns:
            Absolute path to the test directory
        """
        import os

        test_dir = os.path.join(self.__root_dir, self.__test_yaml["path"])
        if not os.path.exists(test_dir):
            msg = f"Test directory {test_dir} does not exist"
            raise FileNotFoundError(msg)

        abs_path = os.path.abspath(test_dir)
        return abs_path

    def clean(self) -> None:
        """
        Clean the test directory based on the test yaml file

        Returns:
            None
        """
        logger.info(f"Cleaning test directory: {self.__test_directory}")
        if "hotstart" in self.__test_yaml and self.__test_yaml["hotstart"]:
            coldstart_directory = self.__get_test_directory(True, False)
            hotstart_directory = self.__get_test_directory(True, True)
            self.__do_clean(coldstart_directory)
            self.__do_clean(hotstart_directory)
        else:
            self.__do_clean(self.__test_directory)

    def __do_clean(self, test_directory: str) -> None:
        """
        Clean the test directory

        Args:
            test_directory: Test directory to clean
        """

        import os

        if "rm_files" in self.__test_yaml:
            for file in self.__test_yaml["rm_files"]:
                file_path = os.path.join(test_directory, file)
                logger.debug(f"Checking for file: {file_path}")
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Removed file: {file_path}")

        for file in self.__test_yaml["output_files"]:
            file_path = os.path.join(test_directory, file)
            logger.debug(f"Checking for file: {file_path}")
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Removed file: {file_path}")

    def run(self) -> dict:
        """
        Run the test

        Returns:
            True if the test passed, False otherwise
        """
        status = {"overall": {"passed": False}}

        if "hotstart" in self.__test_yaml and self.__test_yaml["hotstart"]:
            logger.info("Starting cold-start portion of the test")
            status["coldstart"] = self.__run_test(has_hotstart=True, is_hotstart=False)
            if not status["coldstart"]["passed"]:
                return status
            self.__copy_hotstart()
            logger.info("Starting hot-start portion of the test")
            status["hotstart"] = self.__run_test(has_hotstart=True, is_hotstart=True)
            status["overall"]["passed"] = (
                status["coldstart"]["passed"] and status["hotstart"]["passed"]
            )
        else:
            status["coldstart"] = self.__run_test(has_hotstart=False, is_hotstart=False)
            status["overall"]["passed"] = status["coldstart"]["passed"]

        return status

    def __copy_hotstart(self) -> None:
        """
        Copy the hot start information from the cold start directory to the hot start directory

        Returns:
            None
        """
        import os
        import shutil

        hotstart_file_options = ["fort.67", "fort.68", "fort.67.nc", "fort.68.nc"]
        test_directory_cold = self.__get_test_directory(
            has_hotstart=True, is_hotstart=False
        )
        test_directory_hot = self.__get_test_directory(
            has_hotstart=True, is_hotstart=True
        )
        for file in hotstart_file_options:
            file_cold = os.path.join(test_directory_cold, file)
            file_binary_cold = os.path.join(test_directory_cold, "PE0000", file)
            file_hot = os.path.join(test_directory_hot, file)
            if os.path.exists(file_cold):
                shutil.copy(file_cold, file_hot)
                logger.info(f"Copied hotstart file: {file_cold} to {file_hot}")
            elif os.path.exists(file_binary_cold):
                shutil.copy(file_binary_cold, file_hot)
                logger.info(f"Copied hotstart file: {file_binary_cold} to {file_hot}")

    def __run_test(self, has_hotstart: bool, is_hotstart: bool) -> dict:
        """
        Run the test

        Args:
            has_hotstart: if the test has a hotstart
            is_hotstart: if the test is a hotstart

        Returns:
            A dictionary with the status of the test
        """
        import os
        import subprocess
        from tqdm import tqdm

        # Current directory
        cwd = os.getcwd()

        # Log file
        log_file = os.path.join(self.__test_directory, "test.log")

        try:

            test_directory = self.__get_test_directory(has_hotstart, is_hotstart)

            # Change to the test directory
            os.chdir(test_directory)

            # If the test is parallel, we need to run adcprep
            if self.__test_yaml["parallel"]:
                self.__prep_simulation()

            progress_bar = tqdm(
                total=100,
                ncols=50,
                file=open(os.devnull, "w"),  # noqa: SIM115
            )

            if self.__test_yaml["parallel"]:
                if "n_writer" in self.__test_yaml:
                    total_cpu = self.__test_yaml["ncpu"] + self.__test_yaml["n_writer"]
                else:
                    total_cpu = self.__test_yaml["ncpu"]

                cmd = [
                    "mpirun",
                    "--allow-run-as-root",
                    "-np",
                    "{:d}".format(total_cpu),
                    self.__executable,
                ]
                if "n_writer" in self.__test_yaml and self.__test_yaml["n_writer"] > 0:
                    cmd += ["-W", "{:d}".format(self.__test_yaml["n_writer"])]
            else:
                cmd = self.__executable

            cmd_string = " ".join(cmd)
            logger.debug(f"Running command: {cmd_string}")
            process = subprocess.Popen(
                cmd,
                shell=False,
                bufsize=1,
                universal_newlines=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )

            percent = 0
            logger.info(progress_bar)
            with open(log_file, "w") as log:
                for line in process.stdout:
                    log.write(line)
                    if "TIME STEP" in line and "ITERATIONS" in line:
                        line = line.strip().split()

                        try: 
                            percent_new = int(float(line[4].split("%")[0]))
                        except ValueError:
                            percent_new = percent

                        if (
                            percent_new % 5 == 0 or percent_new - percent > 10
                        ) and percent_new > percent:
                            percent = percent_new
                            progress_bar.update(percent - progress_bar.n)
                            logger.info(progress_bar)

            return_code = process.wait()

            if return_code == 0 and percent < 100:
                progress_bar.update(100 - progress_bar.n)
                logger.info(progress_bar)

            logger.info(f"Executable completed with return code: {return_code}")

            # Check the return code
            if return_code != 0:
                msg = f"Executable failed with return code: {return_code}"
                raise RuntimeError(msg)

            progress_bar.close()

        finally:
            # Change back to the original directory
            os.chdir(cwd)

        passed, failed_files = self.check_results(has_hotstart, is_hotstart)
        return {"complete": True, "passed": passed, "failed_files": failed_files}

    def __prep_simulation(self) -> None:
        """
        Run the prep executable

        Returns:
            None
        """
        import subprocess

        logger.info(f"Running prep executable: {self.__prep_executable}")
        cmd = [
            self.__prep_executable,
            "--np",
            "{:d}".format(self.__test_yaml["ncpu"]),
            "--partmesh",
        ]
        ret = subprocess.run(
            cmd,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if ret.returncode != 0:
            msg = f"Prep executable failed with return code: {ret.returncode}"
            raise RuntimeError(msg)
        cmd = [
            self.__prep_executable,
            "--np",
            "{:d}".format(self.__test_yaml["ncpu"]),
            "--prepall",
        ]

        cmd_string = " ".join(cmd)
        logger.debug(f"Running command: {cmd_string}")

        ret = subprocess.run(
            cmd,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if ret.returncode != 0:
            msg = f"Prep executable failed with return code: {ret.returncode}"
            raise RuntimeError(msg)

    def __get_test_directory(self, has_hotstart: bool, is_hotstart: bool) -> str:
        """
        Gets the test directory based on the hotstart information

        Args:
            has_hotstart: If the test has a hotstart
            is_hotstart: If the test is a hotstart

        Returns:
            Absolute path to the test directory
        """
        import os

        if has_hotstart and not is_hotstart:
            test_directory = os.path.join(self.__test_directory, "01_cs")
        elif has_hotstart and is_hotstart:
            test_directory = os.path.join(self.__test_directory, "02_hs")
        else:
            test_directory = self.__test_directory
        return test_directory

    def check_results(self, has_hotstart: bool, is_hotstart: bool) -> Tuple[bool, list]:
        """
        Check the results of the test based on the test yaml file

        Args:
            has_hotstart: If the test has a hotstart
            is_hotstart: If the test is a hotstart

        Returns:
            Tuple of (True if the test passed, False otherwise, list of error files)
        """
        import os

        all_passed = True
        error_files = []

        test_directory = self.__get_test_directory(has_hotstart, is_hotstart)

        for file in self.__test_yaml["output_files"]:

            logger.info(f"Checking file: {file}")

            control_file = os.path.join(test_directory, "control", file)
            test_file = os.path.join(test_directory, file)

            if not os.path.exists(control_file):
                msg = f"Control file {control_file} does not exist"
                raise FileNotFoundError(msg)

            if not os.path.exists(test_file):
                msg = f"Test file {test_file} does not exist"
                raise FileNotFoundError(msg)

            # Compare the files
            passed = self.__compare_files(control_file, test_file, self.__tolerance)
            if not passed:
                all_passed = False
                error_files.append(test_file.split("/")[-1].split("\\")[-1])

        if not all_passed:
            logger.error(f"Test {self.__test} failed.")
            logger.error(f"Error files: {error_files}")
        else:
            logger.info(f"Test {self.__test} passed")

        return all_passed, error_files

    @staticmethod
    def __compare_files(control_file: str, test_file: str, tolerance: float) -> bool:
        """
        Compare the control and test files

        Args:
            control_file: Name of the control file
            test_file: Name of the test file
            tolerance: Tolerance for the comparison

        Returns:
            True if the files match within spec, False otherwise
        """
        if control_file.endswith(".nc") and test_file.endswith(".nc"):
            return AdcircTest.__compare_files_netcdf(control_file, test_file, tolerance)
        else:
            return AdcircTest.__compare_files_ascii(control_file, test_file, tolerance)

    @staticmethod
    def __compare_files_netcdf(
        control_file: str, test_file: str, tolerance: float
    ) -> bool:
        """
        Compare the control and test files in netcdf format

        Args:
            control_file: Name of the control file
            test_file: Name of the test file
            tolerance: Tolerance for the comparison

        Returns:
            True if the files match within spec, False otherwise
        """
        control = xr.open_dataset(
            control_file,
            drop_variables=AdcircTest.ADCIRC_DROP_VARIABLES_LIST,
            decode_times=False,
        )
        test = xr.open_dataset(
            test_file,
            drop_variables=AdcircTest.ADCIRC_DROP_VARIABLES_LIST,
            decode_times=False,
        )

        passed_test = AdcircTest.__compare_datasets(control, test, tolerance)

        control.close()
        test.close()

        return passed_test

    @staticmethod
    def __compare_datasets(
        control: xr.Dataset, test: xr.Dataset, tolerance: float
    ) -> bool:
        """
        Compare the control and test datasets using xarray and numpy

        Args:
            control: xarray dataset for the control
            test: xarray dataset for the test
            tolerance: Tolerance for the comparison

        Returns:
            True if the datasets match within spec, False otherwise
        """
        import numpy.testing as npt

        passed = True
        for var in control.variables:
            if var not in test.variables:
                msg = f"Variable {var} not found in test file"
                raise ValueError(msg)

            # Only compare numeric types
            if control[var].dtype.kind not in "fi":
                continue

            if "time_of" in var:
                continue
            else:
                this_tolerance = tolerance

            # Check that the variables are the same and get the maximum difference
            try:
                npt.assert_allclose(
                    control[var], test[var], atol=this_tolerance, equal_nan=True
                )
            except AssertionError:
                max_difference = np.nanmax(
                    np.abs(control[var].to_numpy() - test[var].to_numpy())
                )
                if var != "v":
                    logger.error(
                        f"Error in variable: {var} with tolerance {this_tolerance} and maximum difference: {max_difference}"
                    )
                else:
                    logger.error(
                        f"Error with tolerance {this_tolerance} and maximum difference: {max_difference}"
                    )
                passed = False
        return passed

    @staticmethod
    def __compare_files_ascii(
        control_file: str, test_file: str, tolerance: float
    ) -> bool:
        """
        Compare the control and test files in ascii format

        Args:
            control_file: Name of the control file
            test_file: Name of the test file
            tolerance: Tolerance for the comparison

        Returns:
            True if the files match within spec, False otherwise
        """

        # Get the format of the control file
        control_header = AdcircTest.__get_adcirc_header(control_file)
        test_header = AdcircTest.__get_adcirc_header(test_file)

        if control_header != test_header:
            msg = f"Header information does not match in file: {test_file}"
            raise ValueError(msg)

        passed = True

        with open(control_file, "r") as control, open(test_file, "r") as test:

            # Skip the header since we already have this info
            _ = control.readline()
            _ = control.readline()
            _ = test.readline()
            _ = test.readline()

            for i in range(control_header["snap_count"]):
                (
                    control_result,
                    control_time,
                    control_iteration,
                ) = AdcircTest.__read_adcirc_output_snap(control, control_header)
                (
                    test_result,
                    test_time,
                    test_iteration,
                ) = AdcircTest.__read_adcirc_output_snap(test, test_header)
                if control_time != test_time:
                    msg = f"Time mismatch in file {test_file}"
                    raise ValueError(msg)

                if control_iteration != test_iteration:
                    msg = f"Iteration mismatch in file {test_file}"
                    raise ValueError(msg)

                passed_test = AdcircTest.__compare_datasets(
                    control_result, test_result, tolerance
                )
                if not passed_test:
                    passed = False
                    logger.error(f"Test for file {test_file} failed at output snap {i}")

        return passed

    @staticmethod
    def __get_adcirc_header(file: str) -> dict:
        """
        Get the header information from an ADCIRC output file

        Args:
            file: Name of the file

        Returns:
            Dictionary with the header information
        """
        import os

        if not os.path.exists(file):
            msg = f"File {file} does not exist"
            raise FileNotFoundError(msg)

        header = {}
        with open(file, "r") as f:
            _ = f.readline().strip()
            header_line = f.readline().strip().split()

            header["snap_count"] = int(header_line[0])
            header["node_count"] = int(header_line[1])
            header["output_time_interval"] = float(header_line[2])
            header["output_time_step"] = int(header_line[3])
            header["n_values"] = int(header_line[4])

            header3 = f.readline().strip().split()
            if len(header3) == 2:
                header["is_sparse"] = False
            else:
                header["is_sparse"] = True

        return header

    @staticmethod
    def __read_adcirc_output_snap(
        file_obj, header_obj: dict
    ) -> Tuple[xr.Dataset, float, int]:
        """
        Read an ADCIRC output snap file

        Args:
            file_obj: File object for the ADCIRC output file
            header_obj: Header dictionary for the file

        Returns:
            Tuple of (xarray dataset, time, iteration)
        """
        if header_obj["is_sparse"]:
            return AdcircTest.__read_adcirc_output_snap_sparse(file_obj, header_obj)
        else:
            return AdcircTest.__read_adcirc_output_snap_full(file_obj, header_obj)

    @staticmethod
    def __read_adcirc_output_snap_sparse(
        file_obj, header: dict
    ) -> Tuple[xr.Dataset, float, int]:
        """
        Read an ADCIRC output snap file with sparse data

        Args:
            file_obj: File object for the ADCIRC output file
            header: Header dictionary for the file

        Returns:
            Tuple of (xarray dataset, time, iteration)
        """
        line = file_obj.readline().strip().split()
        time = float(line[0])
        iteration = int(line[1])
        n_non_default = int(line[2])
        fill_value = float(line[3])

        dataset = xr.Dataset()
        v = np.full((header["node_count"], header["n_values"]), fill_value)
        for i in range(n_non_default):
            line = file_obj.readline().strip().split()
            node = int(line[0]) - 1
            for j in range(header["n_values"]):
                v[node, j] = float(line[j + 1])
        dataset["v"] = xr.DataArray(
            v,
            dims=["node", "n_values"],
            coords={"node": np.arange(header["node_count"])},
        )

        return dataset, time, iteration

    @staticmethod
    def __read_adcirc_output_snap_full(
        file_obj, header: dict
    ) -> Tuple[xr.Dataset, float, int]:
        """
        Read an ADCIRC output snap file with full data

        Args:
            file_obj: File object for the ADCIRC output file
            header: Header dictionary for the file

        Returns:
            Tuple of (xarray dataset, time, iteration)
        """
        line = file_obj.readline().strip().split()
        time = float(line[0])
        iteration = int(line[1])

        dataset = xr.Dataset()
        v = np.full((header["node_count"], header["n_values"]), np.nan)
        for i in range(header["node_count"]):
            line = file_obj.readline().strip().split()
            for j in range(header["n_values"]):
                v[i, j] = float(line[j])
        dataset["v"] = xr.DataArray(
            v,
            dims=["node", "n_values"],
            coords={"node": np.arange(header["node_count"])},
        )
        return dataset, time, iteration

    def plot(self, status: dict) -> None:
        """
        Plot the results of the test

        Args:
            status: Dictionary with the status of the tests (coldstart, hotstart)

        Returns:
            None
        """
        if "hotstart" in self.__test_yaml and self.__test_yaml["hotstart"]:
            coldstart_directory = self.__get_test_directory(True, False)
            hotstart_directory = self.__get_test_directory(True, True)
            if status["coldstart"]["complete"]:
                logger.info("Plotting cold-start results")
                self.__plot_simulation(coldstart_directory)
            if status["coldstart"]["passed"] and status["hotstart"]["complete"]:
                logger.info("Plotting hot-start results")
                self.__plot_simulation(hotstart_directory)
        else:
            if status["coldstart"]["complete"]:
                logger.info("Plotting test results")
                test_directory = self.__get_test_directory(False, False)
                self.__plot_simulation(test_directory)

    def __plot_simulation(self, test_directory: str) -> None:
        """
        Plot the simulation results in the test directory

        Args:
            test_directory: Test directory to plot the results
        """
        import os

        for file in self.__test_yaml["output_files"]:
            if "max" in file or "min" in file:
                mesh_file = os.path.join(test_directory, "fort.14")
                test_file = os.path.join(test_directory, file)
                control_file = os.path.join(test_directory, "control", file)
                AdcircTest.plot_max_files(
                    self.__test,
                    mesh_file,
                    test_file,
                    control_file,
                    test_directory,
                    self.__is_geographic,
                    self.__is_global,
                )
            elif "fort.61" in file or "fort.62" in file:
                test_file = os.path.join(test_directory, file)
                control_file = os.path.join(test_directory, "control", file)
                AdcircTest.plot_station_files(
                    self.__test, test_file, control_file, test_directory
                )

    @staticmethod
    def plot_max_files(
        test_name: str,
        mesh_file: str,
        test_file: str,
        control_file: str,
        output_directory: str,
        is_geographic: bool,
        is_global: bool,
    ) -> None:
        """
        Plot the maximum difference between two files

        Args:
            test_name: Name of the test
            mesh_file: Name of the mesh file
            test_file: Name of the test file
            control_file: Name of the control file
            output_directory: Directory to output the plots
            is_geographic: If the mesh is in geographic coordinates
            is_global: If the mesh is global

        Returns:
            None
        """
        import os
        import matplotlib.pyplot as plt

        logger.info(f"Plotting peak values for file: {test_file}")

        control_data, test_data, var = AdcircTest.__get_test_data(
            mesh_file, control_file, test_file
        )
        max_diff = np.abs(test_data[var].to_numpy() - control_data[var].to_numpy())[
            0, :, 0
        ]

        # ... Make a histogram plot of the test results
        fig, ax = plt.subplots()
        ax.hist(max_diff, bins=100)
        ax.set_xlabel("Max Difference")
        ax.set_ylabel("Frequency")
        ax.grid(True)
        ax.set_title(f"Test: {test_name}, Max Difference for {var}")
        plt.savefig(os.path.join(output_directory, f"max_diff_{var}_histogram.png"))
        plt.close(fig)

        fig, ax = plt.subplots()
        ax.hist(test_data[var][0, :, 0], bins=100)
        ax.set_xlabel("Max Value")
        ax.set_ylabel("Frequency")
        ax.grid(True)
        ax.set_title(f"Test: {test_name}, Max Value for {var}")
        plt.savefig(os.path.join(output_directory, f"max_value_{var}_histogram.png"))
        plt.close(fig)

        x = control_data["x"].to_numpy()
        y = control_data["y"].to_numpy()

        # Contour the data with symmetrical limits around the max difference
        diff = (
            control_data[var].to_numpy()[0, :, 0] - test_data[var].to_numpy()[0, :, 0]
        )

        # Compute the value of the 95th percentile difference
        max_diff = np.nanmax(np.abs(diff))
        max_val = np.nanmax(test_data[var].to_numpy()[0, :, 0])
        min_val = np.nanmin(test_data[var].to_numpy()[0, :, 0])

        if max_val == min_val:
            min_val -= 0.1
            max_val += 0.1
            max_95 = max_val
            min_5 = min_val
        else:
            valid_points = np.where(~np.isnan(test_data[var].to_numpy()[0, :, 0]))
            valid_data = test_data[var].to_numpy()[0, :, 0][valid_points]
            max_95 = np.nanpercentile(valid_data, 95)
            min_5 = np.nanpercentile(valid_data, 5)
            if max_95 == min_5:
                min_5 -= 0.1
                max_95 += 0.1

        if max_diff == 0:
            min_percentile_95 = -0.1
            max_percentile_95 = 0.1
        else:
            valid_points = np.where(~np.isnan(diff))
            valid_diff = diff[valid_points]
            percentile_95 = np.nanpercentile(valid_diff, 95)
            if percentile_95 == 0.0:
                percentile_95 = 0.1
            min_percentile_95 = min(percentile_95,-percentile_95)
            max_percentile_95 = max(percentile_95,-percentile_95)

        diff_contour_levels = np.linspace(min_percentile_95, max_percentile_95, 100)
        diff_ticks = np.linspace(min_percentile_95, max_percentile_95, 11)
        contour_levels = np.linspace(min_5, max_95, 100)
        contour_ticks = np.linspace(min_5, max_95, 11)

        if is_geographic:
            AdcircTest.__plot_maps_geographic(
                test_name,
                x,
                y,
                test_data,
                control_data,
                diff,
                var,
                contour_levels,
                contour_ticks,
                diff_contour_levels,
                diff_ticks,
                output_directory,
                is_global,
            )
        else:
            AdcircTest.__plot_data_cartesian(
                test_name,
                var,
                x,
                y,
                test_data,
                control_data,
                diff,
                contour_levels,
                contour_ticks,
                diff_contour_levels,
                diff_ticks,
                output_directory,
            )

    @staticmethod
    def __plot_data_cartesian(
        test_name: str,
        var: str,
        x: np.ndarray,
        y: np.ndarray,
        test_data: xr.Dataset,
        control_data: xr.Dataset,
        diff: np.ndarray,
        contour_levels: np.ndarray,
        contour_ticks: np.ndarray,
        diff_contour_levels: np.ndarray,
        diff_ticks: np.ndarray,
        output_directory: str,
    ):
        """
        Plot the data in cartesian coordinates

        Args:
            test_name: Name of the test
            var: Variable to plot
            x: X coordinates
            y: Y coordinates
            test_data: Test data
            control_data: Control data
            diff: Difference between test and control data
            contour_levels: Contour levels for the test data
            contour_ticks: Contour ticks for the test data
            diff_contour_levels: Contour levels for the difference
            diff_ticks: Contour ticks for the difference
            output_directory: Output directory for the plots

        Returns:
            None
        """
        import os
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots()
        ax.set_aspect("equal")
        tri = Triangulation(x, y, control_data["element"] - 1)
        percentile_95 = np.nanpercentile(np.abs(diff), 95)
        min_5 = np.nanpercentile(test_data[var].to_numpy()[0, :, 0], 5)
        max_95 = np.nanpercentile(test_data[var].to_numpy()[0, :, 0], 95)

        if percentile_95 == 0.0:
            percentile_95 = 0.1

        # If there are less than 1000 elements, plot the triangles
        if control_data["element"].size < 1000:
            ax.triplot(tri, lw=0.5, color="black")
            alpha = 0.7
        else:
            alpha = 1.0

        # ... Generate a mask for the nan values
        tri_masked = AdcircTest.get_masked_triangulation(tri, diff)
        diff_contour = ax.tricontourf(
            tri_masked,
            diff,
            cmap="bwr",
            extend="both",
            levels=diff_contour_levels,
            alpha=alpha,
            vmin=-percentile_95,
            vmax=percentile_95,
        )
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.grid(True)
        cbar = plt.colorbar(
            diff_contour, orientation="vertical", ax=ax, ticks=diff_ticks
        )
        cbar.set_label("Difference")
        ax.set_title(f"Max Difference for {var}")
        plt.savefig(os.path.join(output_directory, f"max_diff_{var}_contour.png"))
        plt.close(fig)

        # Plot the test data
        fig, ax = plt.subplots()
        ax.set_aspect("equal")
        tri_masked = AdcircTest.get_masked_triangulation(
            tri, test_data[var].to_numpy()[0, :, 0]
        )
        contour = ax.tricontourf(
            tri_masked,
            test_data[var].to_numpy()[0, :, 0],
            cmap="viridis",
            levels=contour_levels,
            alpha=alpha,
            vmin=min_5,
            vmax=max_95,
        )
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.grid(True)
        ax.set_title(f"Test: {test_name}, {var}")
        cbar = plt.colorbar(contour, orientation="vertical", ax=ax, ticks=contour_ticks)
        cbar.set_label(var)
        plt.savefig(
            os.path.join(output_directory, f"test_{var}_contour.png"),
            dpi=300,
            bbox_inches="tight",
        )
        plt.close(fig)

    @staticmethod
    def __plot_maps_geographic(
        test_name: str,
        x: np.ndarray,
        y: np.ndarray,
        test_data: xr.Dataset,
        control_data: xr.Dataset,
        diff: np.ndarray,
        var: str,
        contour_levels: np.ndarray,
        contour_ticks: np.ndarray,
        diff_contour_levels: np.ndarray,
        diff_ticks: np.ndarray,
        output_directory: str,
        is_global: bool,
    ):
        """
        Plot the data on a map

        Args:
            test_name: Name of the test
            x: X coordinates
            y: Y coordinates
            test_data: Test data
            control_data: Control data
            diff: Difference between test and control data
            var: Variable to plot
            contour_levels: Contour levels for the test data
            contour_ticks: Contour ticks for the test data
            diff_contour_levels: Contour levels for the difference
            diff_ticks: Contour ticks for the difference
            output_directory: Output directory for the plots
            is_global: If the mesh is global

        Returns:
            None
        """
        import os
        import pyproj
        import matplotlib.pyplot as plt
        from matplotlib.tri import Triangulation, LinearTriInterpolator
        from mpl_toolkits.basemap import Basemap

        x_min = np.nanmin(test_data["x"].to_numpy())
        x_max = np.nanmax(test_data["x"].to_numpy())
        y_min = np.nanmin(test_data["y"].to_numpy())
        y_max = np.nanmax(test_data["y"].to_numpy())
        parallels = np.linspace(y_min, y_max, 5)
        meridians = np.linspace(x_min, x_max, 5)
        parallels = np.round(parallels, 1)
        meridians = np.round(meridians, 1)
        crs_wgs = pyproj.CRS("EPSG:4326")
        crs_stereo = pyproj.CRS("EPSG:32661")
        transformer_toster = pyproj.Transformer.from_crs(
            crs_wgs, crs_stereo, always_xy=True
        )
        x_s, y_s = transformer_toster.transform(x, y)
        # Interpolate the data onto a regular grid
        x_g, y_g = np.meshgrid(
            np.linspace(np.min(x), np.max(x), 500),
            np.linspace(np.min(y), np.max(y), 500),
        )
        x_sg, y_sg = transformer_toster.transform(x_g, y_g)
        tri = Triangulation(x_s, y_s, control_data["element"] - 1)
        diff_zi = LinearTriInterpolator(tri, diff)(x_sg, y_sg)
        zi = LinearTriInterpolator(tri, test_data[var].to_numpy()[0, :, 0])(x_sg, y_sg)
        fig, ax = plt.subplots()

        if x_max - x_min > 100:
            res = "i"
        elif x_max - x_min > 30:
            res = "h"
        else:
            res = "f"

        if is_global:
            m = Basemap(
                projection="robin",
                lon_0=(x_min + x_max) / 2,
                lat_0=(y_min + y_max) / 2,
                llcrnrlon=x_min,
                llcrnrlat=y_min,
                urcrnrlon=x_max,
                urcrnrlat=y_max,
                resolution=res,
            )
        else:
            m = Basemap(
                projection="merc",
                lon_0=(x_min + x_max) / 2,
                lat_0=(y_min + y_max) / 2,
                llcrnrlon=x_min,
                llcrnrlat=y_min,
                urcrnrlon=x_max,
                urcrnrlat=y_max,
                resolution=res,
            )
        m.drawcoastlines()
        m.drawcountries()
        m.drawparallels(parallels, labels=[1, 0, 0, 0])
        m.drawmeridians(meridians, labels=[0, 0, 0, 1])
        x_m, y_m = m(x_g, y_g)
        m.contourf(
            x_m, y_m, diff_zi, levels=diff_contour_levels, cmap="bwr", extend="both"
        )
        cbar = m.colorbar(location="right", ticks=diff_ticks)
        cbar.set_label("Difference")
        ax.set_title(f"Max Difference for {var}")
        plt.savefig(os.path.join(output_directory, f"max_diff_{var}_contour.png"))
        plt.close(fig)

        fig, ax = plt.subplots()
        if is_global:
            m = Basemap(
                projection="robin",
                lon_0=(x_min + x_max) / 2,
                lat_0=(y_min + y_max) / 2,
                llcrnrlon=x_min,
                llcrnrlat=y_min,
                urcrnrlon=x_max,
                urcrnrlat=y_max,
                resolution=res,
            )
        else:
            m = Basemap(
                projection="merc",
                lon_0=(x_min + x_max) / 2,
                lat_0=(y_min + y_max) / 2,
                llcrnrlon=x_min,
                llcrnrlat=y_min,
                urcrnrlon=x_max,
                urcrnrlat=y_max,
                resolution=res,
            )
        m.drawcoastlines()
        m.drawcountries()
        m.drawparallels(parallels, labels=[1, 0, 0, 0])
        m.drawmeridians(meridians, labels=[0, 0, 0, 1])
        x_m, y_m = m(x_g, y_g)
        m.contourf(x_m, y_m, zi, levels=contour_levels, cmap="viridis", extend="both")
        cbar = m.colorbar(location="right", ticks=contour_ticks)
        cbar.set_label(var)
        ax.set_title(f"Test: {test_name}, {var}")
        plt.savefig(
            os.path.join(output_directory, f"test_{var}_contour.png"),
            dpi=300,
            bbox_inches="tight",
        )
        plt.close(fig)

    @staticmethod
    def plot_station_files(
        test_name: str, test_file: str, control_file: str, output_directory: str
    ) -> None:
        """
        Plot the station files for the test and control

        Args:
            test_name: Name of the test
            test_file: Name of the test file
            control_file: Name of the control file
            output_directory: Path to the output directory

        Returns:
            None
        """
        import os
        import matplotlib.pyplot as plt

        logger.info(f"Plotting station data for file: {test_file}")

        control_data, test_data, var = AdcircTest.__get_test_data(
            None,
            control_file,
            test_file,
            timeseries=True,
        )

        control_time = control_data["time"].to_numpy() / 86400.0
        test_time = test_data["time"].to_numpy() / 86400.0

        for i in range(control_data["node"].size):

            if var == "u-vel":
                var_name = "uv_mag"
            else:
                var_name = var

            if control_data[var].shape[2] == 2:
                control_var = np.sqrt(
                    control_data[var][:, i, 0].to_numpy() ** 2
                    + control_data[var][:, i, 1].to_numpy() ** 2
                )
                test_var = np.sqrt(
                    test_data[var][:, i, 0].to_numpy() ** 2
                    + test_data[var][:, i, 1].to_numpy() ** 2
                )
            else:
                control_var = control_data[var][:, i, 0].to_numpy()
                test_var = test_data[var][:, i, 0].to_numpy()

            fig, ax = plt.subplots()
            ax.plot(control_time, control_var, label="Control")
            ax.plot(test_time, test_var, label="Test")
            ax.set_xlabel("Time (days)")
            ax.set_ylabel(var_name)
            ax.grid(True)
            ax.legend()
            ax.set_title(f"Station {i}, {var_name}, Test: {test_name}")
            plt.savefig(
                os.path.join(output_directory, f"station_{i}_{var_name}.png"),
                dpi=300,
                bbox_inches="tight",
            )
            plt.close(fig)

    @staticmethod
    def __get_test_data(
        mesh_file: Union[str, None],
        control_file: str,
        test_file: str,
        timeseries: bool = False,
    ) -> Tuple[xr.Dataset, xr.Dataset, str]:
        """
        Get the test data for the control and test files

        Args:
            mesh_file: Mesh file
            control_file: Control file
            test_file: Test file
            timeseries: If the files are time series

        Returns:
            Tuple of (control data, test data, variable)
        """
        var = AdcircTest.__get_adcirc_variable(test_file)
        if test_file.endswith(".nc"):
            test_data = AdcircTest.__get_netcdf_data(test_file, var)
        else:
            test_data = AdcircTest.__get_ascii_data(
                mesh_file, test_file, var, timeseries
            )
        if control_file.endswith(".nc"):
            control_data = AdcircTest.__get_netcdf_data(control_file, var)
        else:
            control_data = AdcircTest.__get_ascii_data(
                mesh_file, control_file, var, timeseries
            )
        return control_data, test_data, var

    @staticmethod
    def __get_adcirc_variable(test_file: str) -> str:
        """
        Get the ADCIRC variable based on the test file

        Args:
            test_file: Name of the test file

        Returns:
            Variable name
        """
        if "maxele" in test_file:
            var = "zeta_max"
        elif "maxvel" in test_file:
            var = "vel_max"
        elif "maxwvel" in test_file:
            var = "wind_max"
        elif "minpr" in test_file:
            var = "pressure_min"
        elif "swan_HS_max" in test_file:
            var = "swan_HS_max"
        elif "swan_TPS_max" in test_file:
            var = "swan_TPS_max"
        elif "fort.61" in test_file:
            var = "zeta"
        elif "fort.62" in test_file:
            var = "u-vel"
        else:
            msg = f"Variable not known for file {test_file}"
            raise ValueError(msg)
        return var

    @staticmethod
    def __get_netcdf_data(file: str, variable: str) -> xr.Dataset:
        """
        Get the data from a netcdf ADCIRC output file

        Args:
            file: Name of the file
            variable: Variable to extract

        Returns:
            xarray dataset
        """
        temp_dataset = xr.open_dataset(
            file,
            drop_variables=AdcircTest.ADCIRC_DROP_VARIABLES_LIST,
            decode_times=False,
        )

        dataset = xr.Dataset(
            {
                "time": temp_dataset["time"],
                "x": temp_dataset["x"],
                "y": temp_dataset["y"],
            }
        )

        if "element" in temp_dataset:
            dataset["element"] = temp_dataset["element"]

        if variable == "u-vel":
            u = temp_dataset["u-vel"].to_numpy()
            v = temp_dataset["v-vel"].to_numpy()
            uv = np.full((u.shape[0], u.shape[1], 2), np.nan)
            uv[:, :, 0] = u
            uv[:, :, 1] = v

            dataset[variable] = xr.DataArray(
                data=uv,
                dims=["time", "node", "n_values"],
            )
        else:
            data = temp_dataset[variable].to_numpy()

            if len(data.shape) == 1:
                data_shaped = data.reshape((1, data.shape[0], 1))
            elif len(data.shape) == 2:
                data_shaped = data.reshape((data.shape[0], data.shape[1], 1))
            else:
                data_shaped = data
            dataset[variable] = xr.DataArray(
                data=data_shaped, dims=["time", "node", "n_values"]
            )

        return dataset

    @staticmethod
    def __get_ascii_data(
        mesh_file: str, file: str, variable: str, timeseries: bool
    ) -> xr.Dataset:
        """
        Get the data from an ascii ADCIRC output file

        Args:
            mesh_file: Mesh file
            file: Name of the file
            variable: Variable name
            timeseries: If the file is a time series

        Returns:
            xarray dataset
        """

        if mesh_file is not None:
            with open(mesh_file, "r") as f:
                _ = f.readline()
                header = f.readline().strip().split()
                node_count = int(header[1])
                element_count = int(header[0])
                nodes = np.zeros((node_count, 3))
                elements = np.zeros((element_count, 3))
                for i in range(node_count):
                    line = f.readline().strip().split()
                    nodes[i, 0] = float(line[1])
                    nodes[i, 1] = float(line[2])
                    nodes[i, 2] = float(line[3])

                for i in range(element_count):
                    line = f.readline().strip().split()
                    elements[i, 0] = int(line[2])
                    elements[i, 1] = int(line[3])
                    elements[i, 2] = int(line[4])

        header = AdcircTest.__get_adcirc_header(file)

        if mesh_file and header["node_count"] != node_count:
            msg = f"Node count mismatch in file {file}"
            raise ValueError(msg)

        dataset = xr.Dataset()

        if timeseries:
            snap_count = header["snap_count"]
        else:
            snap_count = 1

        with open(file, "r") as f:
            _ = f.readline()
            _ = f.readline()
            data = np.full(
                (snap_count, header["node_count"], header["n_values"]), np.nan
            )
            time_data = np.zeros(snap_count)
            if header["is_sparse"]:
                for t in range(snap_count):
                    line = f.readline().strip().split()
                    n_non_default = int(line[2])
                    fill_value = float(line[3])
                    for i in range(n_non_default):
                        line = f.readline().strip().split()
                        node = int(line[0])
                        for j in range(header["n_values"]):
                            val = float(line[j + 1])
                            if val <= fill_value:
                                val = np.nan
                            data[t, node, j] = val
            else:
                for t in range(snap_count):
                    line = f.readline().strip().split()
                    time_data[t] = float(line[0])
                    for i in range(header["node_count"]):
                        line = f.readline().strip().split()
                        for j in range(header["n_values"]):
                            val = float(line[j + 1])
                            if val < -999.0:
                                val = np.nan
                            data[t, i, j] = val

        if mesh_file is not None:
            dataset["x"] = xr.DataArray(nodes[:, 0], dims=["node"])
            dataset["y"] = xr.DataArray(nodes[:, 1], dims=["node"])
            dataset["depth"] = xr.DataArray(nodes[:, 2], dims=["node"])
            dataset["element"] = xr.DataArray(elements, dims=["element", "nvertex"])

        dataset[variable] = xr.DataArray(
            data,
            dims=["time", "node", "n_values"],
            coords={"time": np.arange(snap_count)},
        )
        dataset["time"] = xr.DataArray(time_data, dims=["time"])

        return dataset

    @staticmethod
    def get_masked_triangulation(t: Triangulation, data: np.array) -> Triangulation:
        """
        Get a masked triangulation based on the data

        Args:
            t: Triangulation
            data: Data

        Returns:
            Masked triangulation
        """
        masked_nodes = np.where(np.isnan(data))[0]
        mask = np.full(t.triangles.shape[0], False)
        for i in range(t.triangles.shape[0]):
            if np.any(np.isin(t.triangles[i, :], masked_nodes)):
                mask[i] = True
        return Triangulation(t.x, t.y, t.triangles, mask=mask)
