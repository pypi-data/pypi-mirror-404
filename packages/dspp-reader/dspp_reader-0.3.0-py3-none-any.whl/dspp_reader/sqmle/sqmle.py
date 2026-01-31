import json

import astropy.units as u
import datetime
import os
import re
import pandas as pd
import socket
import logging
import sys

import requests

from astropy.units import Quantity
from pathlib import Path
from requests.exceptions import ConnectionError
from time import sleep
from zoneinfo import ZoneInfo

from dspp_reader.tools import Device, Site
from dspp_reader.tools.generics import augment_data, clean_data, get_filename

logger = logging.getLogger()

READ = b'rx\r\n'
READ_WITH_SERIAL_NUMBER = b'Rx\r\n'
REQUEST_CALIBRATION_INFORMATION = b'cx\r\n'
UNIT_INFORMATION_REQUEST = b'ix\r\n'


class SQMLE(object):
    def __init__(self,
                 site_id: str = '',
                 site_name: str = '',
                 site_timezone: str = '',
                 site_latitude: str = '',
                 site_longitude: str = '',
                 site_elevation: str = '',
                 sun_altitude: float = -10,
                 device_type:str = 'sqm-le',
                 device_id:str = None,
                 device_altitude:float = None,
                 device_azimuth:float = None,
                 device_ip:str = None,
                 device_port=10001,
                 device_window_correction:float = 0,
                 number_of_reads=3,
                 reads_spacing=5,
                 reads_frequency=30,
                 read_all_the_time:bool = False,
                 save_to_file=True,
                 save_to_database=False,
                 post_to_api=False,
                 save_files_to: Path = os.getcwd(),
                 api_endpoint: str = '',
                 file_format: str = "tsv",):
        self.site_id = site_id
        self.site_name = site_name
        self.site_timezone = site_timezone
        self.site_latitude = site_latitude
        self.site_longitude = site_longitude
        self.site_elevation = site_elevation
        self.sun_altitude = sun_altitude
        self.device_type = device_type
        self.device_id = device_id
        self.device_port = device_port
        self.device_altitude = device_altitude
        self.device_azimuth = device_azimuth
        self.device_ip = device_ip
        self.device_window_correction = device_window_correction

        self.number_of_reads = number_of_reads
        self.reads_spacing = reads_spacing
        self.reads_frequency = reads_frequency
        self.read_all_the_time = read_all_the_time
        self.save_to_file = save_to_file
        self.save_to_database = save_to_database
        self.post_to_api = post_to_api
        self.save_files_to = Path(save_files_to)
        self.file_format = file_format
        self.api_endpoint = api_endpoint
        self.separator = ''
        if self.file_format == "tsv":
            self.separator = "\t"
        elif self.file_format == "csv":
            self.separator = ","
        elif self.file_format == "txt":
            self.separator = " "
        else:
            self.separator = " "

        self.site = None
        if all([self.site_id, self.site_name, self.site_timezone, self.site_latitude, self.site_longitude, isinstance(float(self.site_elevation), float)]):
            self.site = Site(
                id=self.site_id,
                name=self.site_name,
                latitude=self.site_latitude,
                longitude=self.site_longitude,
                elevation=self.site_elevation,
                timezone=self.site_timezone)
        else:
            logger.error(f"Not enough site info provided: Please provide: site_id, site_name, site_timezone, site_latitude, site_longitude, site_elevation")

        self.device = None
        if all([self.device_type,
                self.device_id,
                self.device_port,
                isinstance(float(self.device_altitude), float),
                isinstance(float(self.device_azimuth), float),
                self.device_ip,
                self.device_port]):
            self.device = Device(
                serial_id=self.device_id,
                type=self.device_type,
                altitude=self.device_altitude,
                azimuth=self.device_azimuth,
                window_correction=self.device_window_correction,
                site=self.site,
                ip=self.device_ip,
                port=self.device_port,
            )
        else:
            logger.error("Not enough information to define device")

        if self.save_to_file:
            if not os.path.exists(self.save_files_to):
                try:
                    os.makedirs(self.save_files_to)
                    logger.info(f"Created directory {self.save_files_to}")
                except OSError:
                    logger.error(f"Could not create directory {self.save_files_to}")
                    sys.exit(1)
            logger.info(f"Data will be saved to {self.save_files_to}")

    def __call__(self):
        try:
            while True:
                if self.device:
                    if self.device.site:
                        next_period_start, next_period_end, time_to_next_start, time_to_next_end = self.device.site.get_time_range(sun_altitude=self.sun_altitude)
                        if time_to_next_end > time_to_next_start and not self.read_all_the_time:
                            logger.debug(
                                f"Next Sunset is at {next_period_start.strftime('%Y-%m-%d %H:%M:%S %Z (UTC%z)')}")
                            hours = int(time_to_next_start.sec // 3600)
                            minutes = int((time_to_next_start.sec % 3600) // 60)
                            seconds = int(time_to_next_start.sec % 60)

                            try:
                                self._send_command(command=UNIT_INFORMATION_REQUEST)
                                message = f"Waiting for {hours:02d} hours {minutes:02d} minutes {seconds:02d} seconds until next sunset {next_period_start.to_datetime(timezone=ZoneInfo(self.device.site.timezone)).strftime('%Y-%m-%d %H:%M:%S')} {self.device.site.timezone} "
                                if logger.getEffectiveLevel() == logging.DEBUG:
                                    logger.debug(message)
                                else:
                                    print(f"\r{message}", end="", flush=True)
                            except OSError as e:
                                error_message = f"Socket error: {e}. The device may be unavailable."
                                if logger.getEffectiveLevel() == logging.DEBUG:
                                    logger.debug(error_message)
                                else:
                                    print(f"\033[2K\r{error_message}", end="", flush=True)

                            continue
                    else:
                        logger.warning(f"No device has been defined, this program will continue reading continuously.")

                    data = self.get_data_point()

                    if not any([self.save_to_file, self.save_to_database, self.post_to_api]):
                        logger.warning(f"Data will not be stored in any way...")
                        sleep(3)

                    if self.save_to_file:
                        self._write_to_txt(data=data)
                    if self.save_to_database:
                        self._write_to_database(data=data)
                    if self.post_to_api:
                        self._post_to_api(data=data)

                    last_datapoint = datetime.datetime.now(datetime.UTC)
                    logger.info(f"Last Datapoint recorded at {last_datapoint.strftime('%Y-%m-%d %H:%M:%S %Z')} or localtime {last_datapoint.astimezone(ZoneInfo(self.device.site.timezone)).strftime('%Y-%m-%d %H:%M:%S %Z')}.")
                    for i in range(self.reads_frequency):
                        print(f"\r\rNext read in {self.reads_frequency - i} seconds...", end="", flush=True)
                        sleep(1)
                    print("")
                else:
                    if not self.device:
                        logger.error(f"A device is needed to be able to continue")
        except KeyboardInterrupt:
            logger.info("SQM-LE stopped by user")
        except ConnectionRefusedError:
            logger.info("SQM-LE connection refused")

    def get_data_point(self):
        timestamp = datetime.datetime.now(datetime.UTC)
        data = {}
        measurements = []
        while len(measurements) < self.number_of_reads:
            try:

                logger.debug(f"Reading {len(measurements) + 1} of {self.number_of_reads} samples...")
                data = self._send_command(command=READ_WITH_SERIAL_NUMBER)
                logger.debug(f"Response: {data}")

                parsed_data = self._parse_data(data=data, command=READ_WITH_SERIAL_NUMBER)

                corrected_data = self.__apply_window_correction(data=parsed_data)

                measurements.append(corrected_data)
                if self.device.serial_id:
                    if self.device.serial_id != parsed_data['serial_number']:
                        logger.warning(
                            f"Serial number mismatch: {self.device.serial_id} != {parsed_data['serial_number']}")
                sleep(self.reads_spacing)

            except IndexError as e:
                logger.error(f"Error parsing data: Key error: {e}", exc_info=logger.getEffectiveLevel() == logging.DEBUG)
                sleep(self.reads_spacing)
                continue
            except ValueError as e:
                logger.error(f"Error parsing data: ValueError: {e}", exc_info=logger.getEffectiveLevel() == logging.DEBUG)
                sleep(self.reads_spacing)
                continue


        if len(measurements) == 1:
            data = measurements[0]
        elif len(measurements) > 1:
            data = self.__average_data(measurements=measurements, command=READ_WITH_SERIAL_NUMBER)

        augmented_data = augment_data(data=data, timestamp=timestamp, device=self.device)

        return augmented_data

    def _send_command(self, command):
        while True:
            try:
                logger.debug(f"Creating socket connection for {self.device.type} {self.device.serial_id}")
                with socket.create_connection((self.device.ip, self.device.port), timeout=5) as sock:
                    logger.debug(f"Created socket connection for {self.device.type} {self.device.serial_id}")
                    sock.sendall(command)
                    sleep(1)
                    data = sock.recv(1024)
                    return data.decode()
            except OSError as e:
                timeout = 20
                logger.error(
                    f"{datetime.datetime.now().astimezone()}: Unable to connect to {self.device.serial_id} at {self.device.ip}:{self.device.port}: {e}")
                for i in range(1, timeout + 1, 1):
                    print(f"\rAttempting again in {timeout - i} seconds...", end="", flush=True)
                    sleep(1)
                print("")
            except UnicodeDecodeError as e:
                logger.error(f"Error decoding data: {e}")
                sleep(1)


    def __apply_window_correction(self, data):
        data['magnitude'] = data['magnitude'] + self.device_window_correction * u.mag
        return data

    def _parse_data(self, data, command):
        if len(data) == 0:
            raise ValueError("No data has been read")
        data = data.strip().split(',')
        if command == READ:
            if len(data) != 6:
                raise ValueError(f"The command {command.decode().strip()} expects 6 values, but got {len(data)}")
            return {
                'type': data[0],
                'magnitude' : float(re.sub('m', '', data[1])) * u.mag,
                'frequency' : float(re.sub('Hz', '', data[2])) * u.Hz,
                'period_count' : int(re.sub('c', '', data[3])) * u.count,
                'period_seconds' : float(re.sub('s', '', data[4])) * u.second,
                'temperature' : float(re.sub('C', '', data[5])) * u.C,
            }
        elif command == READ_WITH_SERIAL_NUMBER:
            if len(data) != 7:
                raise ValueError(f"The command {command.decode().strip()} expects 7 values, but got {len(data)}")
            response_type = data[0]
            if response_type != 'r':
                raise ValueError(f"Invalid response type {response_type}, the command {command.decode().strip()} expected a type `r`")
            magnitude = float(re.sub('m', '', data[1])) * u.mag
            frequency = float(re.sub('Hz', '', data[2])) * u.Hz
            period_count = int(re.sub('c', '', data[3])) * u.count
            period_seconds = float(re.sub('s', '', data[4])) * u.second
            temperature = float(re.sub('C', '', data[5])) * u.C
            serial_number = str(int(data[6]))

            return {
                'type': response_type,
                'magnitude' : magnitude,
                'frequency' : frequency,
                'period_count' : period_count,
                'period_seconds' : period_seconds,
                'temperature' : temperature,
                'serial_number' : serial_number,
            }
        elif command == REQUEST_CALIBRATION_INFORMATION:
            if len(data) != 6:
                raise ValueError(f"The command {command.decode().strip()} expects 6 values, but got {len(data)}")
            return {
                'type': data[0],
                'magnitude_offset_calibration': float(data[1]),
                'dark_period': float(data[2]),
                'temperature_light_calibration': float(data[3]),
                'magnitude_offset_manufacturer': float(data[4]),
                'temperature_dark_calibration': float(data[5]),
            }
        elif command == UNIT_INFORMATION_REQUEST:
            if len(data) != 5:
                raise ValueError(f"The command {command.decode().strip()} expects 5 values, but got {len(data)}")
            return {
                'type': data[0],
                'protocol_number': data[1],
                'model_number': data[2],
                'feature_number': data[3],
                'serial_number': data[4],
            }
        else:
            logger.error(f"Unknown command: {command.decode().strip()}")
            return data

    def __average_data(self, measurements, command):
        if len(measurements) == 0:
            raise ValueError("No data has been read")
        else:
            logger.debug(f"Average data from {len(measurements)} measurements")
        if command not in [READ, READ_WITH_SERIAL_NUMBER]:
            raise NotImplementedError(f"Command {command.decode().strip()} does not support value averaging")

        df = pd.DataFrame(measurements)
        print(df)
        response_type = df['type'].unique()
        if len(response_type) != 1:
            raise ValueError(
                f"Data is not clean, received multiple data type: {' '.join(response_type)}")
        # Guille should work here
        magnitude = df['magnitude'].mean()
        frequency = df['frequency'].mean()
        period_count = df['period_count'].mean()
        period_seconds = df['period_seconds'].mean()
        temperature = df['temperature'].mean()

        if command == READ:
            return {
                'type': response_type[0],
                'magnitude': magnitude,
                'frequency': frequency,
                'period_count': period_count,
                'period_seconds': period_seconds,
                'temperature': temperature,
            }
        elif command == READ_WITH_SERIAL_NUMBER:
            serial_number = df['serial_number'].unique()
            if len(serial_number) != 1:
                raise ValueError(f"Data is not clean, received multiple serial number: {' '.join(serial_number)}")

            return {
                'type': response_type[0],
                'magnitude': magnitude,
                'frequency': frequency,
                'period_count': period_count,
                'period_seconds': period_seconds,
                'temperature': temperature,
                'serial_number': serial_number[0],
            }
        else:
            raise ValueError(f"Unknown command: {command.decode().strip()}")

    def __get_header(self, data, filename):
        columns = []
        units = []
        for key in data.keys():
            columns.append(key)
            if isinstance(data[key], Quantity):
                units.append(f"# {key}: {data[key].unit}\n")
        return f"# Filename {filename}\n{''.join(units)}# {self.separator.join(columns)}\n"

    def __get_line_for_plain_text(self, data):
        fields = []
        for key in data.keys():
            if isinstance(data[key], Quantity):
                fields.append(str(data[key].value))
            else:
                fields.append(str(data[key]))
        return f"{self.separator.join(fields)}\n"


    def _write_to_txt(self, data):
        filename = get_filename(
            save_files_to=self.save_files_to,
            device_name=self.device.serial_id,
            device_type='sqmle',
            file_format=self.file_format)
        if not os.path.exists(filename):
            header = self.__get_header(data=data, filename=filename)
            with open(filename, 'w') as f:
                f.write(header)
        data_line = self.__get_line_for_plain_text(data=data)
        with open(filename, "a") as f:
            f.write(data_line)
            logger.info(f"Data point written to {filename}")

    def _write_to_database(self, data):
        pass

    def _post_to_api(self, data):
        cleaned_data = clean_data(data)
        reorganized_data = self.__organize_for_api(data=cleaned_data)
        print(json.dumps(reorganized_data, indent=4))

        max_failed_attempts = 5
        failed_attempts = 0
        while failed_attempts <= max_failed_attempts:
            try:
                response = requests.post(self.api_endpoint, json=reorganized_data)
                if response.status_code == 201:
                    logger.info(f"Successfully created new entry in API")
                    return
                else:
                    logger.error(f"Failed to create new entry in API, Status Code: {response.status_code}")
                    failed_attempts += 1
                    sleep(1)
            except ConnectionError as e:
                logger.error(f"Failed to create new entry in API, Error {e}")
                failed_attempts += 1
                sleep(1)

    def __organize_for_api(self, data):

        return {
            'type': data['type'],
            'magnitude': data['magnitude'],
            'frequency': data['frequency'],
            'period_count': data['period_count'],
            'period_seconds': data['period_seconds'],
            'temperature': data['temperature'],
            'timestamp': data['timestamp'],
            'device' : {
                'type': data['device'],
                'serial_number': data['serial_number'],
                'altitude': data['altitude'],
                'azimuth': data['azimuth'],
                'site': {
                    'id': data['site'],
                    'name': self.device.site.name,
                    'latitude': data['latitude'],
                    'longitude': data['longitude'],
                    'elevation': data['elevation'],
                    'timezone': data['timezone'],
                }
            },

        }
