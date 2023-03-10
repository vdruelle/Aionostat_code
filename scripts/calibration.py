# Helper file to calibrate the hardware

import time
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress
from interface import Interface


def calibrate_OD(
        interface: Interface,
        filename: str,
        nb_standards: int,
        vials: list = list(range(1, 16)),
        nb_measures: int = 10,
        lag: float = 0.1,
        voltage_threshold: float = 4.8) -> None:
    """Function to perform the calibration of the OD measurment. It is done by measuring some standard with
    known OD in each of the vial slots. It is suggested to use 4 standards that span the whole range of
    measurable OD.
    Once the procedure is complete, shows a plot with the results and saves a file with the fit parameters.

    Args:
        interface: Interface object from the interface.py file.
        filename: name of the save file.
        nb_standards: number of OD standard to calibrate on.
        vials: list of vials to calibrate. Defaults to list(range(1, 16)).
        nb_measure: number of voltage measures to average for each data point. Defaults to 10.
        lag: time between voltage measures in seconds. Defaults to 0.1.

    Returns:
        fit_parameters: the fit parameters from the fit of the OD to voltage relation.
    """
    assert nb_standards >= 2, "At least 2 OD standards are needed for the calibration."

    ODs = []
    voltages = np.zeros((nb_standards, len(vials)))

    # Measuring the voltage for all vial + OD standard combo
    for ii in range(nb_standards):  # iterating over all standards
        no_valid_standard = True
        while no_valid_standard:
            print()
            cur_OD = input(f"Enter OD of standard {ii+1}: ")
            ODs.append(float(cur_OD))
            no_valid_standard = False

        for jj, vial in enumerate(vials):  # iterating over all vials for the current OD standard
            input("   Place OD standard in vial slot " + str(vial) + ", press enter when done")
            interface.switch_light(True)
            voltages[ii][jj] = interface.measure_OD(vial, lag, nb_measures)  # Measuring voltage
            interface.switch_light(False)
            print(f"   Mean voltage measured: {voltages[ii][jj]}V")

    print()
    print("Calibration manipulation complete. Calculating voltage -> OD conversion.")
    ODs = np.array(ODs)
    fit_parameters = np.zeros((len(vials), 2))  # first columns are slope, second are intercepts

    # Computing the fit for all vials
    for ii, vial in enumerate(vials):
        good_measurements = voltages[:, ii] < voltage_threshold
        if good_measurements.sum() > 1:
            slope, intercept, _, _, _ = linregress(ODs[good_measurements], voltages[good_measurements, ii])
        else:
            print("Less than 2 good measurements, also using saturated measurements for vial" + str(vial))
            slope, intercept, _, _, _ = linregress(ODs, voltages[:, ii])
        fit_parameters[ii, 0] = slope
        fit_parameters[ii, 1] = intercept

    print(f"Calibration completed. Saving results in file {filename} and plotting results.")
    np.savetxt(filename, fit_parameters)

    # make figure showing calibration
    plt.figure()
    plt.plot(ODs, voltages, '.-')
    plt.xlabel('OD standard [a.u.]')
    plt.ylabel('Voltage [V]')
    plt.show()


def calibrate_pumps(interface: Interface, filename: str, pumps: list, dt: float = 10):
    """Function to perform the calibration of the pumps. For now it is done by connecting all the pumps and
    putting their inlet in water and their outlet on the scale. Then each pump is run for dt seconds and the
    user is asked for the new weight. Pumping rates are inferred from the differenc in weights.

    Args:
        interface: Interface object from interface.py file.
        filename: name of the save file.
        pumps: list of the pumps to calibrate.
        dt: Pumping time for the calibration. Defaults to 10.
    """
    weights = np.zeros((2, len(pumps)))  # Pumps are columns, first line is weight before and second is after

    print(f"Starting pump calibration for pumps {pumps}.")
    print("Put inlet of all pumps in water. Put outlet of pumps in vial on a balance")

    input("When the setup is ready press enter. It will run all the pumps for 10s to fill the tubing.")
    for pump in enumerate(pumps):
        interface._run_pump(pump, 10)

    weight = input("Initial weight of vial: ")
    for ii, pump in enumerate(pumps):  # iterate over all pumps and asks for weights
        print(f"Calibrating pump {pump}:")
        weights[0, ii] = weight
        interface._run_pump(pump, dt)
        weight = input("    Measured weight of vial: ")
        weights[1, ii] = weight

    print()
    print("Calibration manipulation complete. Computing pumping rate.")

    # calculate pump_rate and save to file
    pump_rates = (weight[1,:] - weight[0,:]) / dt

    print(f"Saving data in {filename}.")
    np.savetxt(filename, pump_rates)


if __name__ == "__main__":
    interface = Interface()
    calibrate_OD(interface, "test.txt", nb_standards=3, vials=[1, 2], nb_measures=1)
