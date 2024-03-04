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
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Callable, TYPE_CHECKING

from tinydb import Query, TinyDB

from sgs.utils import fix_languages, logger, write_ruleset

if TYPE_CHECKING:
    import argparse
    from tinydb.table import Table

LOG = logging.getLogger(__name__)


def get_set_from_arg(arg: Optional[list[str]]) -> Optional[set[str]]:
    if arg is None:
        return None

    result = set()
    for param in arg:
        result |= {part.strip() for part in param.split(',')}

    return result


@dataclass
class FilterConfig:
    languages: Optional[set[str]]
    categories: Optional[set[str]]
    severities: Optional[set[str]]
    origins: Optional[set[str]]
    include_empty: bool

    @staticmethod
    def from_args(args: argparse.Namespace) -> 'FilterConfig':
        languages = get_set_from_arg(args.language)
        if languages:
            languages = fix_languages(languages)

        categories = get_set_from_arg(args.category)

        severities = get_set_from_arg(args.severity)

        origins = get_set_from_arg(args.origin)

        return FilterConfig(
            include_empty=args.include_empty,
            languages=languages,
            categories=categories,
            severities=severities,
            origins=origins,
        )


def filter_rule_by_languages(config: FilterConfig) -> Callable[[list[str]], bool]:
    def filter_fn(langs: list[str]) -> bool:
        if not langs:
            return config.include_empty
        return any(lang in langs for lang in config.languages)
    return filter_fn


def filter_rules(rules: Table, config: FilterConfig) -> list[dict]:
    Rule = Query()  # noqa: N806 - Better readability

    q = Rule.id.exists()

    if config.languages is not None:
        q &= Rule.languages.test(filter_rule_by_languages(config))

    if config.categories is not None:
        category = Rule.category.one_of(config.categories)
        if config.include_empty:
            category |= Rule.category == None  # noqa: E711 - Required for TinyDB queries
        q &= category

    if config.severities is not None:
        severity = Rule.severity.one_of(config.severities)
        if config.include_empty:
            severity |= Rule.severity == None  # noqa: E711 - Required for TinyDB queries
        q &= severity

    if config.origins is not None:
        q &= Rule.source.one_of(config.origins)

    return rules.search(q)


def search(args: argparse.Namespace, db: TinyDB) -> None:
    rules = db.table('rules')
    config = FilterConfig.from_args(args)

    result = filter_rules(rules, config)

    if len(result) == 0:
        logger.info('No rules found matching your search criteria')
        return

    if args.output == '-':
        path = None
        stream = sys.stdout
    else:
        path = Path(args.output)
        stream = path.open('w+')

    write_ruleset(result, stream)

    if path is not None:
        logger.info(f'Successfully written {len(result)} rules to {path.absolute()}')
