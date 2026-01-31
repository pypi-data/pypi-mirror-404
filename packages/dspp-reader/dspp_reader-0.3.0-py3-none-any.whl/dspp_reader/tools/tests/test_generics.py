import astropy.units as u
import datetime

from astropy.units import Quantity
from pathlib import Path
from unittest import TestCase

from unittest.mock import patch, Mock

from dspp_reader.tools import Device, Site
from dspp_reader.tools.generics import augment_data, clean_data, get_args, get_filename


class TestCleanData(TestCase):

    def test_instance_of_quantity(self):
        ten_meters = 10 * u.meter

        cleaned_data = clean_data(ten_meters)

        self.assertIsInstance(ten_meters, Quantity)
        self.assertEqual(cleaned_data, ten_meters.value)


    def test_dictionary(self):
        data = {
            "distance": 10 * u.meter,
            "count": 5
        }

        cleaned_data = clean_data(data)

        self.assertEqual(cleaned_data['distance'], data['distance'].value)
        self.assertEqual(cleaned_data['count'], data['count'])

    def test_list_or_tuple(self):
        data = [10 * u.meter, 5 * u.count]
        distance, counts = clean_data(data)

        self.assertEqual(distance, data[0].value)
        self.assertEqual(counts, data[1].value)

    def test_float_value(self):
        data = 50

        cleaned_data = clean_data(data)

        self.assertEqual(cleaned_data, data)


class TestAugmentData(TestCase):

    def setUp(self):
        self.data = {}
        self.timestamp = datetime.datetime.now()

    def test_without_device(self):
        augmented_data = augment_data(self.data, self.timestamp)

        self.assertIn('timestamp', augmented_data.keys())
        self.assertIn('localtime', augmented_data.keys())

    def test_with_device_and_no_site(self):
        device = Device(serial_id='1234', type='sqmle', altitude=90, azimuth=90, site=None, window_correction=0.1, ip='0.0.0.0', port=10001)
        augmented_data = augment_data(self.data, self.timestamp, device=device)

        self.assertIn('timestamp', augmented_data.keys())
        self.assertIn('localtime', augmented_data.keys())
        self.assertIn('device', augmented_data.keys())
        self.assertIn('altitude', augmented_data.keys())
        self.assertIn('azimuth', augmented_data.keys())
        self.assertNotIn('site', augmented_data.keys())
        self.assertNotIn('timezone', augmented_data.keys())
        self.assertNotIn('latitude', augmented_data.keys())
        self.assertNotIn('longitude', augmented_data.keys())
        self.assertNotIn('elevation', augmented_data.keys())


    def test_with_device_and_site(self):
        site = Site(id='ctio', name='CTIO', latitude=-70, longitude=-30, elevation=2300, timezone='America/Santiago')
        device = Device(serial_id='1234', type='sqmle', altitude=90, azimuth=90, site=site, window_correction=0.1,
                        ip='0.0.0.0', port=10001)

        augmented_data = augment_data(self.data, self.timestamp, device=device)

        self.assertIn('timestamp', augmented_data.keys())
        self.assertIn('localtime', augmented_data.keys())
        self.assertIn('device', augmented_data.keys())
        self.assertIn('altitude', augmented_data.keys())
        self.assertIn('azimuth', augmented_data.keys())
        self.assertIn('site', augmented_data.keys())
        self.assertIn('timezone', augmented_data.keys())
        self.assertIn('latitude', augmented_data.keys())
        self.assertIn('longitude', augmented_data.keys())
        self.assertIn('elevation', augmented_data.keys())


class TestGetFilename(TestCase):

    def setUp(self):
        self.save_files_to = Path('/some/path/to/save/files')
        self.device_name = 'dev_9999'
        self.device_type = 'test'
        self.file_format = 'tsv'

        local_timezone = datetime.timezone(datetime.timedelta(hours=-4))
        self.before_noon = datetime.datetime(year=2026, month=1, day=10, hour=10, tzinfo=local_timezone)
        self.right_at_noon = datetime.datetime(year=2026, month=1, day=10, hour=12, tzinfo=local_timezone)
        self.after_noon = datetime.datetime(year=2026, month=1, day=10, hour=14, tzinfo=local_timezone)

    @patch('dspp_reader.tools.generics.datetime.datetime')
    def test_filename_before_noon(self, mock_datetime_class):
        mock_datetime_class.side_effect = lambda *args, **kw: datetime.datetime(*args, **kw) if args or kw else Mock()

        mock_datetime_class.now.return_value.astimezone.return_value = self.before_noon
        filename = get_filename(save_files_to=self.save_files_to,
                                device_name=self.device_name,
                                device_type=self.device_type,
                                file_format=self.file_format)
        correct_date = self.before_noon - datetime.timedelta(days=1)
        expected_filename = f"{correct_date.strftime('%Y%m%d')}_{self.device_type}_{self.device_name}.{self.file_format}"
        expected_filename_full_path = Path(self.save_files_to, expected_filename)
        self.assertEqual(filename, expected_filename_full_path)

    @patch('dspp_reader.tools.generics.datetime.datetime')
    def test_filename_after_noon(self, mock_datetime_class):
        mock_datetime_class.side_effect = lambda *args, **kw: datetime.datetime(*args, **kw) if args or kw else Mock()

        mock_datetime_class.now.return_value.astimezone.return_value = self.after_noon
        filename = get_filename(save_files_to=self.save_files_to,
                                device_name=self.device_name,
                                device_type=self.device_type,
                                file_format=self.file_format)

        expected_filename = f"{self.after_noon.strftime('%Y%m%d')}_{self.device_type}_{self.device_name}.{self.file_format}"
        expected_filename_full_path = Path(self.save_files_to, expected_filename)
        self.assertEqual(filename, expected_filename_full_path)

    @patch('dspp_reader.tools.generics.datetime.datetime')
    def test_filename_right_at_noon(self, mock_datetime_class):
        mock_datetime_class.side_effect = lambda *args, **kw: datetime.datetime(*args, **kw) if args or kw else Mock()

        mock_datetime_class.now.return_value.astimezone.return_value = self.right_at_noon
        filename = get_filename(save_files_to=self.save_files_to,
                                device_name=self.device_name,
                                device_type=self.device_type,
                                file_format=self.file_format)

        expected_filename = f"{self.right_at_noon.strftime('%Y%m%d')}_{self.device_type}_{self.device_name}.{self.file_format}"
        expected_filename_full_path = Path(self.save_files_to, expected_filename)
        self.assertEqual(filename, expected_filename_full_path)

#
# class TestGetArgs(TestCase):
#
#     def test_sqm_args(self):
#         # args = get_args(device_type='sqm-le')
#         #
#         # print(args)
#         # self.fail()
#         pass
#
#
#     def test_tess_args(self):
#         pass
