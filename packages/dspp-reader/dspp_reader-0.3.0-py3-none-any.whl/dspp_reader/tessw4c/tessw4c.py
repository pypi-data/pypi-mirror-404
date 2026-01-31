import datetime
import json
import os
import socket
import logging
import sys
from json import JSONDecodeError
from time import sleep

from pathlib import Path
from zoneinfo import ZoneInfo

import requests

from dspp_reader.tools import Site, Device
from dspp_reader.tools.generics import augment_data, get_filename

logger = logging.getLogger(__name__)

class TESSW4C(object):

    def __init__(self,
                 site_id: str = '',
                 site_name: str = '',
                 site_timezone: str = '',
                 site_latitude: str = '',
                 site_longitude: str = '',
                 site_elevation: str = '',
                 sun_altitude: float = -10,
                 device_type: str = 'tess-w4c',
                 device_id: str = '',
                 device_altitude: float = 0,
                 device_azimuth: float = 0,
                 device_ip: str = '0.0.0.0',
                 device_port: int = 23,
                 use_udp: bool = False,
                 udp_bind_ip: str='0.0.0.0',
                 udp_port: int =2255,
                 read_all_the_time: bool = False,
                 save_to_file: bool=True,
                 save_to_database: bool=False,
                 post_to_api: bool=False,
                 save_files_to: Path = os.getcwd(),
                 api_endpoint: str = '',
                 file_format: str = 'tsv'):
        self.site_id = site_id
        self.site_name = site_name
        self.site_timezone = site_timezone
        self.site_latitude = site_latitude
        self.site_longitude = site_longitude
        self.site_elevation = site_elevation
        self.sun_altitude = sun_altitude
        self.use_udp = use_udp
        self.udp_bind_ip = udp_bind_ip
        self.udp_port = udp_port
        self.device_type = device_type
        self.device_id = device_id
        self.device_altitude = device_altitude
        self.device_azimuth = device_azimuth
        self.device_ip = device_ip
        self.device_port = device_port
        self.read_all_the_time = read_all_the_time
        self.save_to_file = save_to_file
        self.save_to_database = save_to_database
        self.post_to_api = post_to_api
        self.save_files_to = Path(save_files_to)
        self.timestamp = datetime.datetime.now(datetime.UTC)
        self.logger_level = logger.getEffectiveLevel()
        self.separator = ' '
        self.file_format = file_format
        self.api_endpoint = api_endpoint
        if self.file_format == 'tsv':
            self.separator = '\t'
        elif self.file_format == 'csv':
            self.separator = ','
        elif self.file_format == 'txt':
            self.separator = ' '

        self.site = None
        if all([self.site_id, self.site_name, self.site_timezone, self.site_latitude, self.site_longitude, self.site_elevation]):
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
                isinstance(float(self.device_altitude), float),
                isinstance(float(self.device_azimuth), float),
                self.device_ip,
                self.device_port]):
            self.device = Device(
                serial_id=self.device_id,
                type=self.device_type,
                altitude=self.device_altitude,
                azimuth=self.device_azimuth,
                site=self.site,
                ip=self.device_ip,
                port=self.device_port)
        else:
            logger.error(f"Not enough information to define device")

        self.udp_socket = None
        self.tcp_socket = None
        if self.use_udp:
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.bind((self.udp_bind_ip, self.udp_port))
            logger.debug(f"{self.device_type.upper()} initialized, listening on {self.udp_bind_ip}:{self.udp_port}")
        elif self.device:
            while not self.tcp_socket:
                try:
                    logger.debug(f"Creating socket connection for {self.device.serial_id}")
                    self.tcp_socket = socket.create_connection((self.device.ip, self.device.port), timeout=5)
                    logger.info(f"Created socket connection for {self.device.serial_id}")
                except OSError as e:
                    timeout = 20
                    print(f"\r{datetime.datetime.now().astimezone()}: Unable to connect to {self.device.serial_id} at {self.device.ip}:{self.device.port}: {e}")
                    for i in range(1, timeout + 1, 1):
                        print(f"\rAttempting again in {timeout - i} seconds...", end="", flush=True)
                        sleep(1)
        else:
            logger.error(f"Either use_udp or provide information to define a device.")
            logger.info(f"Use the argument  --help for more information")
            sys.exit(1)

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
            logger.info(f"{self.device_type.upper()} started using {'UDP' if self.use_udp else 'TCP/IP'}")
            if self.site:
                logger.info(f"Using site {self.site.name} at {self.site.latitude} {self.site.longitude}")
            else:
                logger.info(f"No site was defined or provided")
            if self.device:
                logger.info(f"Using device type {self.device.type}  Serial ID {self.device.serial_id} configured with Altitude {self.device.altitude} and Azimuth {self.device.azimuth}")
            last_message_id = None
            while True:
                if self.device and self.device.site:
                    next_period_start, next_period_end, time_to_next_start, time_to_next_end = self.device.site.get_time_range(sun_altitude=self.sun_altitude)
                    if time_to_next_end > time_to_next_start and not self.read_all_the_time:
                        logger.debug(f"Next Sunset is at {next_period_start.strftime('%Y-%m-%d %H:%M:%S %Z (UTC%z)')}")
                        hours = int(time_to_next_start.sec // 3600)
                        minutes = int((time_to_next_start.sec % 3600) // 60)
                        seconds = int(time_to_next_start.sec % 60)

                        try:
                            if self.tcp_socket:
                                self.tcp_socket.recv(1024)
                            message = f"Waiting for {hours:02d} hours {minutes:02d} minutes {seconds:02d} seconds until next sunset {next_period_start.to_datetime(timezone=ZoneInfo(self.device.site.timezone)).strftime('%Y-%m-%d %H:%M:%S')} {self.device.site.timezone} "
                            if self.logger_level == logging.DEBUG:
                                logger.debug(message)
                            else:
                                print(f"\r{message}", end="", flush=True)
                        except OSError as e:
                            error_message = f"Socket error: {e}. The device may be unavailable."
                            if self.logger_level == logging.DEBUG:
                                logger.debug(error_message)
                            else:
                                print(f"\033[2K\r{error_message}", end="", flush=True)

                        continue
                else:
                    logger.warning(f"No device has been defined, this program will continue reading continuously.")

                self.timestamp = datetime.datetime.now(datetime.UTC)

                if self.use_udp:
                    data, addr = self.udp_socket.recvfrom(2048)
                    parsed_data = json.loads(data.decode('utf-8'))
                    device_serial = parsed_data['name']
                    logger.info(
                        f"{self.device_type.upper()} received message {parsed_data['udp']} at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')} from ip address: {addr[0]}, device name: {self.device.serial_id if self.device else parsed_data['name']}")
                    if self.device and (device_serial != self.device.serial_id):
                            logger.warning(f"Provided device serial id {device_serial} does not match device retuned serial id {self.device.serial_id}")
                else:
                    try:
                        data = self.tcp_socket.recv(1024)
                        parsed_data = json.loads(data.decode('utf-8'))
                        message_id = parsed_data['udp']
                        if message_id != last_message_id:
                            message = f"Last data point retrieved at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')} or localtime {self.timestamp.astimezone(ZoneInfo(self.device.site.timezone)).strftime('%Y-%m-%d %H:%M:%S %Z')}"
                            if self.logger_level == logging.DEBUG:
                                logger.debug(message)
                            else:
                                print(f"\r{message}", end="", flush=True)
                            last_message_id = message_id
                        else:
                            logger.debug(f"Message id {message_id} skipped at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')} because it has the same id as previous message ({last_message_id}).)")
                            continue
                    except TimeoutError:
                        logger.error(f"Socket timed out")
                        continue
                    except JSONDecodeError as e:
                        logger.error(f"Error parsing data: {e}")
                        continue

                augmented_data = augment_data(data=parsed_data, timestamp=self.timestamp, device=self.device)
                if self.save_to_file:
                    self._write_to_file(data=augmented_data)
                if self.save_to_database:
                    self._write_to_database(data=augmented_data)
                if self.post_to_api:
                    self._post_to_api(data=augmented_data)

        except KeyboardInterrupt:
            logger.info(f"{self.device_type.upper()} stopped by user")
        finally:
            if self.udp_socket:
                self.udp_socket.close()
            if self.tcp_socket:
                self.tcp_socket.close()

    def __get_header(self, data, filename):
        columns = []
        for key in data.keys():
            if key.startswith('F'):
                for subkey in data[key].keys():
                    columns.append(f"{key}_{subkey}")
            else:
                columns.append(key)
        return f"# File name: {filename}\n# {self.separator.join(columns)}\n"

    def __get_line_for_plain_text(self, data):
        fields = []
        for key in data.keys():
            if key.startswith('F'):
                for subkey in data[key].keys():
                    fields.append(str(data[key][subkey]))
            else:
                fields.append(str(data[key]))
        return f"{self.separator.join(fields)}\n"

    def _write_to_file(self, data):
        filename = get_filename(
            save_files_to=self.save_files_to,
            device_name=data['name'],
            device_type=data['type'] if 'type' in data else self.device_type,
            file_format=self.file_format)
        if not os.path.exists(filename):
            header = self.__get_header(data=data, filename=filename)
            with open(filename, 'w') as f:
                f.write(header)
        data_line = self.__get_line_for_plain_text(data)
        with open(filename, 'a') as f:
            f.write(data_line)
            logger.debug(f"{self.device_type.upper()} data written to {filename}")

    def _write_to_database(self, data):
        print(data)

    def _post_to_api(self, data):
        organized_data = self.__organize_for_api(data=data)

        max_failed_attempts = 5
        failed_attempts = 0
        while failed_attempts < max_failed_attempts:
            try:
                response = requests.post(self.api_endpoint, json=organized_data)
                if response.status_code == 201:
                    logger.info(f"Successfully posted data to {self.api_endpoint}")
                    return
                else:
                    logger.error(f"Failed to post data to {self.api_endpoint}")
                    failed_attempts += 1
                    sleep(1)
            except ConnectionError:
                logger.error(f"Failed to connect to {self.api_endpoint}")
                failed_attempts += 1
                sleep(1)

    def __organize_for_api(self, data):
        return {
            "message_id": data['udp'],
            "timestamp": data['timestamp'],
            "localtime": data['localtime'],
            "photometer_1": {
                "frequency": data["F1"]['freq'],
                "magnitude": data["F1"]['mag'],
                "zeropoint": data["F1"]['zp']
            }, "photometer_2": {
                "frequency": data["F2"]['freq'],
                "magnitude": data["F2"]['mag'],
                "zeropoint": data["F2"]['zp']
            }, "photometer_3": {
                "frequency": data["F3"]['freq'],
                "magnitude": data["F3"]['mag'],
                "zeropoint": data["F3"]['zp']
            }, "photometer_4": {
                "frequency": data["F4"]['freq'],
                "magnitude": data["F4"]['mag'],
                "zeropoint": data["F4"]['zp']
            },
            "ambient_temperature": data["tamb"],
            "sky_temperature": data["tsky"],
            'device': {
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




if __name__ == '__main__':
    tess = TESSW4C(use_udp=True)
    tess()
