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

import sys
import argparse

from rich.console import Console

from sgs.const import DATA_DIR, CATEGORIES, SEVERITIES

from sgs.database import get_database
from sgs.inspection import inspect
from sgs.search import search
from sgs.utils import logger, build_logger, get_metadata, print_verbose_info, get_version


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog='semgrep-search',
        description='Searches for rules in the semgrep-search database and builds semgrep commands',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    subparsers = parser.add_subparsers(dest='command', required=True)

    def add_commons(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('--update', '-u', action='store_true', default=False,
                            help='Force an update of the database')
        parser.add_argument('-v', '--verbose', dest='verbose', action='count', default=0,
                            help='Enable verbose logging')

    search = subparsers.add_parser('search', help='Search for rules and generate a ruleset to use with semgrep')

    search.add_argument('--language', '-l', action='append',
                        help='The language(s) to filter for. '
                             'Separate multiple languages with comma or providing this argument multiple times')
    search.add_argument('--category', '-c', action='append', choices=CATEGORIES,
                        help='The category(/ies) to filter for. '
                             'Specify multiple categories by providing this argument multiple times')
    search.add_argument('--severity', '-s', action='append', choices=SEVERITIES,
                        help='The severity(/ies) to filter for. '
                             'Specify multiple severities by providing this argument multiple times')
    search.add_argument('--origin', '-o', action='append',
                        help='The origin(s) to select rules from. '
                             'Specify multiple origins by providing this argument multiple times '
                             'or by separating them by comma')
    search.add_argument('--include-empty', '-e', action='store_true', default=False,
                        help='Include rules that do not specify a selected filter at all')
    search.add_argument('--output', '-O', default='rules.yaml',
                        help='Output file that contains all matched rules (- for stdout)')
    add_commons(search)

    inspect = subparsers.add_parser('inspect', help='Print stats about all rules within the database')
    inspect.add_argument('--hide-empty', dest='hide_empty', action='store_true', default=False,
                         help='If set, do not show empty rows in tables')
    add_commons(inspect)

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    build_logger(args)

    # Ensure the data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    db = get_database(args)
    if db is None:
        logger.error('Failed to load the database')
        return 1

    meta = get_metadata(db)
    if not meta:
        logger.warning('Database did not contain valid metadata. This could mean that your database is very old. '
                       'If errors occur, consider updating the database.')
    else:
        Console().print(print_verbose_info(meta))

    if meta['min_version'] is None:
        logger.warning('Database metadata does not specify a minimum semgrep-search version. '
                       'Please consider updating the database.')
    elif get_version() < meta['min_version']:
        logger.warning('Database requires a newer version (%s) of semgrep-search than the installed one (%s). '
                       'Please consider updating your semgrep-search installation.',
                       str(meta['min_version']), str(get_version()))

    match args.command:
        case 'search':
            search(args, db)
        case 'inspect':
            inspect(args, db)

    return 0


if __name__ == '__main__':
    sys.exit(main())
