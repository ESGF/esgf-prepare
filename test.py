#!/usr/bin/env python

import logging
stream_handler=logging.StreamHandler()
formatter = logging.Formatter(fmt='%(levelname)-10s %(asctime)s %(message)s')
stream_handler.setFormatter(formatter)
logging.getLogger().addHandler(stream_handler)
logging.info('salut')
