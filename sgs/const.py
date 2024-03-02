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

from collections import OrderedDict
from pathlib import Path


def generate_aliases(languages: OrderedDict[str, list[str]]) -> dict[str, str]:
    """
    For each language, take all known aliases and generate a lookup table
    """
    lookup_table = {}
    for names in languages.values():
        base = names[0]
        aliases = names[1:]
        for alias in aliases:
            lookup_table.setdefault(alias, base)
    return lookup_table


DATA_DIR = Path.home() / '.cache' / 'semgrep-search'
DB_FILENAME = 'db.json'
DB_FILE = DATA_DIR / DB_FILENAME
CATEGORIES = ('best-practice', 'correctness', 'maintainability', 'performance', 'portability', 'security')
SEVERITIES = ('ERROR', 'INFO', 'WARNING')

LANGUAGES = OrderedDict([
    ('Apex', ['apex']),
    ('Bash', ['bash', 'sh']),
    ('C', ['c']),
    ('Cairo', ['cairo']),
    ('Clojure', ['clojure']),
    ('C++', ['cpp', 'c++']),
    ('C#', ['csharp', 'c#', 'cs']),
    ('Dart', ['dart']),
    ('Dockerfile', ['dockerfile', 'docker']),
    ('Elixir', ['ex', 'elixir']),
    ('Generic', ['generic']),
    ('Go', ['go', 'golang']),
    ('HTML', ['html']),
    ('Java', ['java']),
    ('JavaScript', ['js', 'javascript']),
    ('JSON', ['json']),
    ('Jsonnet', ['jsonnet']),
    ('JSX', ['js', 'javascript']),
    ('Julia', ['julia']),
    ('Kotlin', ['kt', 'kotlin']),
    ('Lisp', ['lisp']),
    ('Lua', ['lua']),
    ('OCaml', ['ocaml']),
    ('PHP', ['php']),
    ('Python', ['python', 'python2', 'python3', 'py']),
    ('R', ['r']),
    ('Ruby', ['ruby']),
    ('Rust', ['rust']),
    ('Scala', ['scala']),
    ('Scheme', ['scheme']),
    ('Solidity', ['solidity', 'sol']),
    ('Swift', ['swift']),
    ('Terraform', ['tf', 'hcl', 'terraform']),
    ('TypeScript', ['ts', 'typescript']),
    ('YAML', ['yaml']),
    ('XML', ['xml']),
])

LANGUAGE_ALIASES = generate_aliases(LANGUAGES)


