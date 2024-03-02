#      Semgrep-Search
#      Copyright (C) 2024  Malte Heinzelmann
#
#      This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#
#      You should have received a copy of the GNU General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from oras.provider import Registry
from tinydb import TinyDB

from sgs.const import DB_FILE, DB_FILENAME
from sgs.utils import logger, measure_time

if TYPE_CHECKING:
    import argparse


class GhcrProvider(Registry):
    def __init__(self) -> None:
        super().__init__('ghcr.io')


def load_local() -> Optional[TinyDB]:
    if not DB_FILE.exists():
        return None
    try:
        return TinyDB(DB_FILE)
    except Exception as e:
        logger.debug(str(e), exec_info=e)
        return None


def update_db() -> Optional[TinyDB]:
    files = GhcrProvider().pull(target='hnzlmnn/semgrep-search-db:latest')
    for file in files:
        path = Path(file)
        if path.name == DB_FILENAME:
            try:
                # load the database to ensure, the file is not broken
                TinyDB(path).close()
            except Exception as e:
                logger.debug(str(e), exec_info=e)
                logger.warning("Updated database couldn't be opened")
                return None
            # Copy the database to the cache location
            shutil.copyfile(path, DB_FILE)
            return load_local()
    logger.error('Could not find the database file in ')
    return None


def get_database(args: argparse.Namespace) -> Optional[TinyDB]:
    # Try to load the local database first
    db = load_local()

    if db is None or args.update:
        if db is not None:
            # Make sure we close the database before running update
            db.close()

        logger.info('Fetching latest database version')

        # Try to update
        with measure_time('Updated database in %s', logging.DEBUG):
            return update_db()

    # No update should occur
    return db
