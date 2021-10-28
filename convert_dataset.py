'''
Lerta Electrical Energy Dataset Converter


'''

import datetime
from inspect import currentframe, getfile, getsourcefile
from os import getcwd
from sys import stdout, getfilesystemencoding

import pandas as pd
import numpy as np
from os.path import join, exists, isdir, dirname, abspath
import yaml


def check_directory_exists(d: str) -> None:
    if not isdir(d):
        raise IOError("Directory '{}' does not exist.".format(d))


def get_module_directory() -> str:
    path_to_this_file = dirname(getfile(currentframe()))
    assert isdir(path_to_this_file), path_to_this_file + ' is not a directory'
    return path_to_this_file


def convert_dataset(input_path: str) -> None:
    """
    Parameters
    ----------
    input_path : str
        The root path of the RAW dataset.
    """

    check_directory_exists(input_path)

    metadata_path = join(get_module_directory(), 'appliance_ids.yaml')
    with open(metadata_path, 'r') as stream:
        metadata = yaml.safe_load(stream)

    for house_name, house_values in metadata.items():
        csv_filename = join(input_path, f'CLEAN_{house_name}.csv')
        if not exists(csv_filename):
            print(f'Converting house: {house_name}.')
            _convert_to_clean(input_path, house_name, house_values)
        else:
            print(f'The  file {house_name} is already converted.')


def _set_index(df: pd.DataFrame) -> pd.DataFrame:
    # Convert column to datetime format and set as index.
    df['datetime'] = pd.to_datetime(df['datetime'])
    df.set_index('datetime', inplace=True)
    # NOTE: Covert to time aware index.
    df = df.tz_convert('Europe/Warsaw')
    return df


def _get_aggregate(power: pd.DataFrame, aggregate_id: str) -> pd.Series:
    """
    This function allows the conversion of raw data to pd.Series containing the index as pd.DatetimeIndex
    and the value as a measurement in [W]
    """
    aggregate = _set_index(power)
    # Get measurement only in power -> [kW].
    aggregate = aggregate[(aggregate['deviceId'] == aggregate_id) & (aggregate['unit'] == 'kW')]
    # A power above 4000000 or below 0 is considered as measurement error and converted to 0.
    aggregate['value'] = np.where((aggregate['value'] > 4000000) | (aggregate['value'] < 0), 0, aggregate['value'])
    # Remove duplicate and resample into 6s. Replace NaN values with the value from the nearest member of the sequence.
    aggregate = aggregate[~aggregate.index.duplicated()]
    aggregate = aggregate.resample(pd.Timedelta(seconds=6)).nearest()
    # Convert [kW] into [W].
    aggregate['value'] = aggregate['value'] * 1000
    aggregate = aggregate.rename(columns={'value': 'AGGREGATE'})

    return aggregate['AGGREGATE']


def _get_device_ids(data) -> np.ndarray:
    """
    Return list of unique values of devices ids.
    """
    return np.unique(data[data['unit'] == 'W']['deviceId'].values)


def _get_values_for_device(data: pd.DataFrame, device_id: str) -> pd.DataFrame:
    """
    This function allows the conversion of raw data to pd.Series containing the index as pd.DatetimeIndex
    and the value as a measurement in [W]
    """
    device = data.loc[(data['deviceId'] == device_id) & (data['unit'] == 'W')]
    device['value'] = np.where((device['value'] > 4000000) | (device['value'] < 0), 0, device['value'])
    device = _find_edges(device['value'])
    device = device[~device.index.duplicated(keep='last')]
    device = device.resample(pd.Timedelta(seconds=6)).nearest()

    return device


def _find_edges(data: pd.Series) -> pd.DataFrame:
    """
    Find index when n is non zero and value of n-1 is 0, then insert new index as (index - 1s) with 0 value
    to avoid problems caused by rare sampling.
    """
    values = data.to_numpy()
    index = data.index.to_numpy()
    values_array = np.array(list(zip(index, values)))
    temp_index = []
    for row in range(values_array.shape[0]):
        if (values_array[row, 1] != 0) and (values_array[row - 1, 1] == 0):
            temp_index.append(values_array[row, 0] + datetime.timedelta(seconds=-1))
    if len(temp_index) == 0:
        return pd.DataFrame(data)
    temp_values = np.array(list(zip(temp_index, np.zeros(len(temp_index)))))
    values_array = np.concatenate((values_array, temp_values))
    values_df = pd.DataFrame(values_array, columns=['datetime', 'value'])
    values_df.set_index('datetime', inplace=True)

    return values_df['value'].sort_index()


def _get_appliances(aggregate: pd.Series, energy: pd.DataFrame, house_values: dict) -> pd.DataFrame:
    """
    A function that creates a specific pd.DataFrame:

    index: pd.DatetimeIndex
    col_0: aggregate measurement value
    col_1-X: appliance measurement value of individual devices.

    """
    appliances = _set_index(energy)
    # Create a list consisting of device id and corresponding DataFrame.
    appliances = [(device, _get_values_for_device(appliances, device)) for device in _get_device_ids(appliances)]
    result = aggregate.to_frame()
    for device_id, data in appliances:
        # Find device name by device id
        device_name = next((name for name, device in house_values.items() if device == device_id), device_id)
        # Attach individual devices to the overall pd.DataFrame.
        result = result.join(data.to_frame().rename(columns={'value': device_name}))
    # Fill NaN values
    result = result.fillna(method='ffill').fillna(method='bfill')

    return result


def _convert_to_clean(input_path: str, house_name: str, house_values: dict) -> None:
    power_data_path = join(input_path, f'{house_name}_power.csv')
    energy_data_path = join(input_path, f'{house_name}_energy.csv')
    if not exists(power_data_path) or not exists(energy_data_path):
        raise RuntimeError('Could not find energy or power raw data. Check dataset.yaml for more information!')
    power = pd.read_csv(power_data_path)
    aggregate = _get_aggregate(power, house_values['AGGREGATE'])
    energy = pd.read_csv(energy_data_path)
    measurements_converted = _get_appliances(aggregate, energy, house_values)
    measurements_converted.index.names = ['Time']
    measurements_converted.to_csv(join(input_path, f'CLEAN_{house_name}.csv'))
