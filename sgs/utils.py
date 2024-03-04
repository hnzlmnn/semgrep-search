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

import datetime
import logging
import sys
from contextlib import contextmanager
from importlib import metadata
from importlib.metadata import PackageNotFoundError
from pathlib import Path
from typing import Union, Tuple, Callable, ContextManager, TextIO, TYPE_CHECKING, Optional

import tomli
from babel.dates import format_datetime
from rich.text import Text
from ruamel.yaml import YAML, CommentedSeq, CommentedMap
from semver import Version

from sgs.const import LANGUAGE_ALIASES

if TYPE_CHECKING:
    import argparse
    from tinydb import TinyDB


def fix_languages(langauges: Union[set[str], list[str]]) -> set[str]:
    """
    Resolves all aliased languages to their base name
    """
    return {LANGUAGE_ALIASES.get(lang, lang) for lang in langauges}


logger = logging.getLogger('semgrep-search')


def build_logger(args: argparse.Namespace) -> None:
    log_format = '%(message)s'

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(logging.Formatter(log_format))
    console_handler.setLevel(logging.DEBUG if args.verbose > 0 else logging.INFO)
    logger.addHandler(console_handler)
    logger.setLevel(logging.DEBUG)


def hours_minutes_seconds(td: datetime.timedelta) -> Tuple[int, int, int]:
    return td.seconds//3600, (td.seconds//60) % 60, td.seconds % 60


def human_readable(td: datetime.timedelta) -> str:
    hours, minutes, seconds = hours_minutes_seconds(td)
    if hours > 0:
        return f'{hours}h{minutes}m{seconds}s'
    if minutes > 0:
        return f'{minutes}m{seconds}s'
    if seconds > 0:
        return f'{seconds}s'
    return f'0.{td.microseconds // 1000}s'


@contextmanager
def measure_time(output: str, level: int = logging.INFO) -> Callable[..., ContextManager[None]]:
    start_time = datetime.datetime.now(datetime.timezone.utc)
    yield
    elapsed_time = datetime.datetime.now(datetime.timezone.utc) - start_time
    logger.log(level, output, human_readable(elapsed_time))


yaml = YAML(typ='rt')


def write_ruleset(rules: list[dict], stream: TextIO) -> None:
    data = CommentedSeq()
    for rule in rules:
        rule_data: CommentedMap = yaml.load(rule['content'])
        rule_data.setdefault('metadata', CommentedMap())

        # Add origin to metadata
        rule_data['metadata'].setdefault('semgrep.dev', CommentedMap())
        rule_data['metadata']['semgrep.dev'].setdefault('rule', CommentedMap())
        rule_data['metadata']['semgrep.dev']['rule']['origin'] = rule['source']

        data.append(rule_data)
    yaml.dump({'rules': data}, stream)


def get_metadata(db: TinyDB) -> Optional[dict]:
    metadata = db.table('meta').all()
    if len(metadata) == 0:
        return None
    metadata = metadata[0]

    created_on = metadata.get('created_on', None)
    version = metadata.get('version', None)
    min_version = metadata.get('min_version', None)
    commit = metadata.get('commit', None)

    if any(var is None for var in [created_on, version, commit]):
        return None

    try:
        return {
            'created_on': datetime.datetime.fromisoformat(created_on),
            'version': Version.parse(version),
            'commit': commit,
            'min_version': Version.parse(min_version) if min_version else None,
        }
    except Exception:
        return None


def print_verbose_info(meta: dict) -> Text:
    info = ['Database was created ']

    if meta['created_on']:
        info += [
            'on ',
            (format_datetime(meta['created_on']), 'blue'),
        ]
    info += [
        ' using semgrep-search-db ',
        (f'v{meta["version"]}', 'green'),
        ' (',
        (meta['commit'], 'cyan'),
        ')',
    ]

    return Text.assemble(*info)


def get_version() -> Version:
    try:
        version = metadata.version('semgrep-search-db')
    except PackageNotFoundError:
        try:
            with Path('pyproject.toml').open('rb') as fin:
                version = tomli.load(fin).get('tool').get('poetry').get('version')
        except Exception:
            version = '0.0.0-dev'
    return Version.parse(version)
