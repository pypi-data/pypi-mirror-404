from typing import Union

from dspp_reader.tools import Site

class Device(object):

    def __init__(self, serial_id: str, type: str, altitude: float, azimuth: float, site: Site,  window_correction:float = 0, ip: Union[str, None] = None, port: Union[int, None] = None):
        self.serial_id = str(serial_id)
        self.type = type
        self.altitude = altitude
        self.azimuth = azimuth
        self.site = site
        self.ip = ip
        self.port = port
        self.window_correction = window_correction
        if self.type in ['smqle', 'sqm-le'] and ip is None and port is None:
            raise ValueError('ip and port must be specified for SQM-LE device')

    def __repr__(self):
        if self.type in ['sqmle', 'sqm-le']:
            return f"Type: {self.type}\nSerial ID: {self.serial_id}\nAlt: {self.altitude}\nAz: {self.azimuth}\nSite: {self.site.name if self.site else 'No site'}\nIP: {self.ip}\nPort: {self.port}\nWindow Correction {self.window_correction}"
        elif self.type in ['tessw4c', 'tess-w4c']:
            return f"Type: {self.type}\nSerial ID: {self.serial_id}\nAlt: {self.altitude}\nAz: {self.azimuth}\nSite: {self.site.name if self.site else 'No site'}\nWindow Correction {self.window_correction}"
        else:
            return f"Device of unknown type: {self.type}"
