import astropy.units as u
import datetime

from astropy.time import Time
from astropy.coordinates import EarthLocation
from pytz import timezone as tz
from astroplan import Observer

class Site(object):
    def __init__(self, id, name, latitude, longitude, elevation, timezone,):
        self.id = id
        self.name = name
        self.latitude = latitude * u.deg
        self.longitude = longitude * u.deg
        self.elevation = elevation * u.m
        self.timezone = timezone
        self.location = EarthLocation.from_geodetic(self.longitude, self.latitude, self.elevation)
        self.observer = Observer(
            name=self.name,
            location=self.location,
            timezone=tz(self.timezone),
            description=self.name)

    def get_time_range(self, sun_altitude:float = -10):
        now = Time(datetime.datetime.now(datetime.UTC))
        # now = Time("2024-12-02 09:00:00")
        reference_time = now
        next_period_start = self.observer.sun_set_time(reference_time, which='next', horizon=sun_altitude * u.deg)
        next_period_end = self.observer.sun_rise_time(reference_time, which='next', horizon=sun_altitude * u.deg)
        time_to_next_start = next_period_start - now
        time_to_next_end = next_period_end - now
        return next_period_start, next_period_end, time_to_next_start, time_to_next_end
