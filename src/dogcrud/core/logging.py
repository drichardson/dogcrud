# SPDX-FileCopyrightText: 2025-present Doug Richardson <git@rekt.email>
# SPDX-License-Identifier: MIT

import logging
import time


class ElapsedTimeFormatter(logging.Formatter):
    def __init__(self):
        super().__init__(fmt="%(elapsed)s [%(levelname)s] %(message)s")
        self.now = time.monotonic
        self.t0 = self.now()

    def format(self, record):
        seconds_since_t0 = self.now() - self.t0
        record.elapsed = f"{seconds_since_t0:.2f}s"
        return super().format(record)


def setup_logger(logger: logging.Logger, level_name: str):
    handler = logging.StreamHandler()
    formatter = ElapsedTimeFormatter()
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.getLevelNamesMapping()[level_name])
    return logger
