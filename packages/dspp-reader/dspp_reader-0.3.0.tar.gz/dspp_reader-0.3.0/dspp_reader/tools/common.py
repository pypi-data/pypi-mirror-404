import logging
import os
import re
import sys
from importlib.metadata import version

import yaml

from dspp_reader.sqmle.sqmle import SQMLE
from dspp_reader.tessw4c import TESSW4C
from dspp_reader.tools import get_args, setup_logging

__version__ = version('dspp-reader')

reader_registry = {
    "sqm-le": SQMLE,
    "tess-w4c": TESSW4C
}

def read_device(device_type:str, config_fields_default: dict, args=None):
    args = get_args(device_type=device_type, args=args)

    if args.config_file_example:
        print("# Add this to a .yaml file, reference it later with --config-file <file_name>.yaml")
        print(yaml.dump(config_fields_default, default_flow_style=False, sort_keys=False))
        sys.exit(0)

    site_config = {}
    if 'config_file' in args.__dict__.keys() and os.path.isfile(args.config_file):
        with open(args.config_file, "r") as f:
            site_config = yaml.safe_load(f) or {}

    config = {}
    for field in config_fields_default.keys():
        if field not in args.__dict__ or not args.__dict__[field]:
            config[field] = site_config.get(field)
        else:
            config[field] = getattr(args, field)
    config["device_type"] = device_type

    setup_logging(debug=args.debug, device_type=device_type, device_id=config["device_id"])
    logger = logging.getLogger()
    logger.info(f"Starting {device_type.upper()} reader, Version: {__version__}")

    invalid_fields = [k for k, v in config.items() if v is None and 'udp' not in k]
    if invalid_fields:
        for field in invalid_fields:
            logger.error(f"Missing argument: --{re.sub('_', '-', field)}")

        logger.info(f"Use --help for more information. Pay attention to --config-file and --config-file-example")
        sys.exit(1)
    logger.info(f"Using the following configuration:\n\n\t{re.sub('\n', '\n\t', yaml.dump(config, sort_keys=False))}")

    cls = reader_registry[device_type]

    try:
        photometer_reader = cls(**config)
        photometer_reader()
    except KeyboardInterrupt:
        print("\n")
        logger.info(f"Exiting {device_type.upper()} reader on user request, Version: {__version__}")
        sys.exit(0)
    except NotImplementedError as e:
        logger.critical(f"Critical error in {device_type.upper()}: {e}")
