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
from typing import TYPE_CHECKING

from babel.dates import format_datetime
from rich import box
from rich.columns import Columns
from rich.console import Console
from rich.table import Table
from rich.text import Text

from sgs.const import LANGUAGES
from sgs.utils import fix_languages

if TYPE_CHECKING:
    import argparse
    from tinydb import TinyDB


def gather_stats(db: TinyDB, args: argparse.Namespace) -> dict:
    rules = db.table('rules')

    origins = {}
    languages = {}

    for rule in rules:
        origin = rule.get('source_name', rule.get('source', None))
        if origin:
            origins.setdefault(origin, 0)
            origins[origin] += 1

        rule_languages = rule.get('languages')
        for language in fix_languages(rule_languages):
            # As fix_languages returns a set, we can be sure, we have no duplicates
            languages.setdefault(language, 0)
            languages[language] += 1

    resolved_languages = {}
    for language, names in LANGUAGES.items():
        base = names[0]
        if args.hide_empty and base not in languages:
            continue
        resolved_languages[language] = languages.get(base, 0)

    return {
        'origins': origins,
        'languages': resolved_languages,
    }

def inspect(args: argparse.Namespace, db: TinyDB) -> None:
    meta = db.table('meta')
    console = Console()

    if len(meta) > 0:
        metadata = meta.all()[0]

        created_on = metadata.get('created_on', None)
        version = metadata.get('version', 'unknown')
        commit = metadata.get('commit', 'unknown')

        info = ['Database was created ']

        if created_on:
            info += [
                'on ',
                (format_datetime(datetime.datetime.fromisoformat(created_on)), 'blue'),
            ]
        info += [
            ' using semgrep-search-db ',
            (f'v{version}', 'green'),
            ' (',
            (commit, 'cyan'),
            ')\n\n',
        ]

        console.print(Text.assemble(*info))

    stats = gather_stats(db, args)

    origins = Table(title='Origin Overview', box=box.SIMPLE)
    origins.add_column('Origin', style='blue', no_wrap=True)
    origins.add_column('Number of rules', style='green', no_wrap=True)

    for origin, num_rules in stats['origins'].items():
        origins.add_row(origin, str(num_rules))

    languages = Table(title='Language Overview', box=box.SIMPLE)
    languages.add_column('Language', style='blue', no_wrap=True)
    languages.add_column('Number of rules', style='green', no_wrap=True)

    for language, num_rules in sorted(stats['languages'].items(), key=lambda item: item[1], reverse=True):
        num_rules = str(num_rules) if num_rules > 0 else Text.assemble((str(num_rules), 'red'))
        languages.add_row(language, num_rules)

    console.print(Columns([origins, languages], equal=False, expand=False))
