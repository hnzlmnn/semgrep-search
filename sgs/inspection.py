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

from typing import TYPE_CHECKING

from rich import box
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
        origin = rule.get('source', rule.get('source', None))
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
        'count': len(rules),
        'origins': origins,
        'languages': resolved_languages,
    }


def inspect(args: argparse.Namespace, db: TinyDB) -> None:
    console = Console()

    stats = gather_stats(db, args)

    console.print(Text.assemble(
        'The database contains ',
        (str(stats['count']), 'green'),
        ' rules in total\n',
    ))

    repos = db.table('repos')
    if len(repos) > 0:
        repo_table = Table(title='Repositories', box=box.SIMPLE, expand=True)

        repo_table.add_column('ID', style='red')
        repo_table.add_column('Name', style='blue')
        repo_table.add_column('License')
        repo_table.add_column('URL', no_wrap=True)
        repo_table.add_column('Number of Rules', style='green')

        for repo in repos:
            url = repo.get('url', '')
            if url:
                url = f'[link={url}]{url}[/link]'
            repo_table.add_row(
                repo.get('id'),
                repo.get('name'),
                repo.get('license', ''),
                url,
                str(stats['origins'].get(repo['id'], 0)),
            )

        console.print(repo_table, no_wrap=False, soft_wrap=False)
    else:
        origins = Table(title='Origin Overview', box=box.SIMPLE)
        origins.add_column('Origin', style='blue', no_wrap=True)
        origins.add_column('Number of rules', style='green', no_wrap=True)

        for origin, num_rules in stats['origins'].items():
            origins.add_row(origin, str(num_rules))

        console.print(origins)

    languages = Table(title='Language Overview', box=box.SIMPLE)
    languages.add_column('Language', style='blue', no_wrap=True)
    languages.add_column('Number of Rules', style='green', no_wrap=True)

    for language, num_rules in sorted(stats['languages'].items(), key=lambda item: item[1], reverse=True):
        num_rules = str(num_rules) if num_rules > 0 else Text.assemble((str(num_rules), 'red'))
        languages.add_row(language, num_rules)

    console.print(languages)
