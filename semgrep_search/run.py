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

import asyncio
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.text import Text
from tinydb import TinyDB

from semgrep_search.runconfig import RunConfig
from semgrep_search.search import filter_rules
from semgrep_search.semgrep import run_semgrep
from semgrep_search.utils import logger, write_ruleset

if TYPE_CHECKING:
    import argparse


def run(args: argparse.Namespace, db: TinyDB) -> None:
    print(args)
    try:
        run = RunConfig.from_args(args)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    do_run(run, db)


def do_run(run: RunConfig, db: TinyDB) -> None:
    if not run.validate_output():
        logger.error('When outputting to stdout, exactly one output format must be selected')
        sys.exit(3)

    if run.binary:
        semgrep = Path(run.binary)
        if not semgrep.exists() or not semgrep.is_file():
            logger.error("Provided path to semgrep is not a valid file")
            sys.exit(1)
        if not os.access(semgrep, os.X_OK):
            logger.error("Provided semgrep file is not executable")
            sys.exit(2)
    else:
        semgrep = shutil.which('semgrep')
        if semgrep is None:
            logger.error("Unable to find semgrep. make sure it's within your PATH or specify the location directly")
            sys.exit(3)
    run.binary = semgrep

    if not run.init_from_code:
        Console().print(
            Text.assemble(*['Hint: This command can also be run by only using ', (run.to_code(), 'blue'), ]))

    with tempfile.NamedTemporaryFile(delete=not run.keep_rules_file, delete_on_close=False, prefix='seamgrep-search-',
                                     suffix='.yaml') as stream:
        if run.rules_file is None:
            rules = db.table('rules')
            result = filter_rules(rules, run.filter_config)

            if len(result) == 0:
                logger.info('No rules found matching your search criteria')
                return

            write_ruleset(result, stream)
            stream.close()
            logger.info(f'Successfully written {len(result)} rules to {stream.name}')
            run.rules_file = Path(stream.name)

        rc = asyncio.run(run_semgrep(run))
        logger.debug(f'rc: {rc}')
