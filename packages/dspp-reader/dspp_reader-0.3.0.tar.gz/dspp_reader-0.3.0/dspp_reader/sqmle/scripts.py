import os

from importlib.metadata import version

from dspp_reader.tools.common import read_device

__version__ = version("dspp-reader")


CONFIG_FIELDS_DEFAULT = {
    "site_id": "ctio",
    "site_name": "Cerro Tololo",
    "site_latitude": -30.169166,
    "site_longitude": -70.804,
    "site_elevation": 2174,
    "site_timezone": "America/Santiago",
    "sun_altitude": -10,
    "device_type": "sqm-le",
    "device_id": "1823",
    "device_altitude": 45,
    "device_azimuth": 0,
    "device_ip": "0.0.0.0",
    "device_port": 10001,
    "device_window_correction": -0.11,
    "number_of_reads": 5,
    "reads_frequency": 30,
    "read_all_the_time": False,
    "save_to_file": True,
    "save_to_database": False,
    "post_to_api": False,
    "save_files_to": os.getcwd(),
    "api_endpoint": "http://localhost:8000/api/sqm-le",
    "file_format": 'tsv',
}


def read_sqmle(args=None):
    read_device(device_type='sqm-le',
                config_fields_default=CONFIG_FIELDS_DEFAULT,
                args=args)
