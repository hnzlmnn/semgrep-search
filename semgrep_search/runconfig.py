import argparse
import math
import os
from pathlib import Path
from typing import Callable, Optional

import base58

from semgrep_search.search import FilterConfig


class BitMapper:
    CONTINUE_BIT = 1 << 7

    @staticmethod
    def split_into_groups(bs: bytes):
        groups = []
        group = []
        for b in bs:
            group.append(b)
            if (b & BitMapper.CONTINUE_BIT) == 0:
                groups.append(group)
                group = []
        if len(group) > 0:
            groups.append(group)
        return groups

    @staticmethod
    def bit_set(the_byte: int, n: int):
        return n < 8 and (the_byte & (1 << n)) == (1 << n)

    @staticmethod
    def get_set_bits_in_group(group: list[int]) -> list[int]:
        bits = []
        for n, b in enumerate(group):
            for i in range(0, 7):
                if BitMapper.bit_set(b, i):
                    bits.append(i + n * 7)

        return bits
    

    @staticmethod
    def numBytes(flag: 'BitFlag', bits: list[int], trim: bool) -> int:
        if trim:
            return max(bits)
        return flag.max_value()


class BitFlag:
    def __init__(self, values: dict[str, int]):
        self._values = values
        self._reverse = {value: key for key, value in values.items()}

    def parse(self, group: list[int]) -> list[str]:
        values: list[str] = []
        for bit in BitMapper.get_set_bits_in_group(group):
            feature = self._reverse.get(bit, None)
            if feature is not None:
                values.append(feature)
        return values

    def build(self, values: list[str], trim: bool = False) -> bytes:
        bits = [self._values.get(value, 0) for value in values]
        max_value = max(bits) if trim else max(self._values.values())
        num_bytes = max(1, math.ceil(max_value / 7))
        b = []

        for i in range(num_bytes):
            # Last byte must not set the continue bit
            byte = BitMapper.CONTINUE_BIT if i < num_bytes - 1 else 0
            
            for j in range(i * 7, (i+1) * 7):
                if j in bits:
                    byte += 1 << (j - (i * 7))
            
            b.append(byte)
        
        return bytes(b)


class RunConfig:
    _CATEGORIES = BitFlag(
        {"null": 0, "best-practice": 1, "correctness": 2, "maintainability": 3, "performance": 4, "portability": 5,
            "security": 6, })
    _LANGUAGES = BitFlag(
        {"apex": 0, "bash": 1, "c": 2, "cairo": 3, "clojure": 4, "cpp": 5, "csharp": 6, "dart": 7, "dockerfile": 8,
            "ex": 9, "generic": 10, "go": 11, "html": 12, "java": 13, "js": 14, "json": 15, "jsonnet": 16, "julia": 17,
            "kt": 18, "lisp": 19, "lua": 20, "ocaml": 21, "php": 22, "python": 23, "r": 24, "ruby": 25, "rust": 26,
            "scala": 27, "scheme": 28, "solidity": 29, "swift": 30, "tf": 31, "ts": 32, "yaml": 33, "xml": 34, })
    _SEVERITIES = BitFlag({"null": 0, "INVENTORY": 1, "INFO": 2, "WARNING": 3, "ERROR": 4, })
    _FEATURES = BitFlag({"export_text": 0, "export_sarif": 1, "export_json": 2, })

    flag_order: list[tuple[BitFlag, Callable[['RunConfig'], list[str]]]] = [
        (_CATEGORIES, lambda self: self.categories),
        (_LANGUAGES, lambda self: self.languages),
        (_SEVERITIES, lambda self: self.severities),
        (_FEATURES, lambda self: self.features),
    ]

    def __init__(self, categories: list[str], languages: list[str], severities: list[str], features: list[str], *,
                 from_code=False, rules_file: Optional[Path]=None, keep_rules_file=None):
        self.categories = categories
        self.languages = languages
        self.severities = severities
        self.features = features
        self.filter_config = FilterConfig.from_config(self)
        self.binary = None
        self.output: Path = None
        self.target: Path = Path('.').absolute()
        self.init_from_code = from_code
        self.rules_file = rules_file
        self.keep_rules_file = keep_rules_file
        
    @staticmethod
    def from_rules_file(file: Path, features: list[str]) -> 'RunConfig':
        if not file.is_file():
            raise ValueError('File not found')
        if not file.exists():
            raise ValueError('File is a directory')
        if not os.access(file, os.R_OK):
            raise ValueError('Permission denied')
        return RunConfig([], [], [], features, from_code=True, rules_file=file, keep_rules_file=True)

    @staticmethod
    def from_code(code: str):
        b = base58.b58decode(code)
        groups = BitMapper.split_into_groups(b)
        return RunConfig(
            *[flag[0].parse(groups[i] if i < len(groups) else []) for i, flag in enumerate(RunConfig.flag_order)],
            from_code=True)

    @staticmethod
    def from_args(args: argparse.Namespace):
        features = list(filter(lambda x: x is not None, [
            'export_text' if args.text else None, 'export_json' if args.json else None,
            'export_sarif' if args.sarif else None, ]))
        if args.rules:
            # We don't need to generate any rules here
            config = RunConfig.from_rules_file(Path(args.rules), features)
        elif args.config:
            config = RunConfig.from_code(args.config)
        else:
            config = RunConfig.from_config(FilterConfig.from_args(args), features)
        if args.binary:
            config.binary = args.binary
        if args.output:
            config.output = Path(args.output).resolve().absolute()
        if args.target:
            config.target = Path(args.target)
        if config.keep_rules_file is None:
            config.keep_rules_file = args.keep_rules_file

        return config

    @staticmethod
    def from_config(config: FilterConfig, features: list[str]):
        return RunConfig(categories=config.categories or [], languages=config.languages or [],
            severities=config.severities or [], features=features, )

    def to_code(self) -> str:
        b = b''.join(flag[0].build(flag[1](self)) for i, flag in enumerate(RunConfig.flag_order))
        return base58.b58encode(b).decode('ascii')

    def validate_output(self) -> bool:
        if self.output != '-':
            return True
        return len(self.output_params()) == 1

    def output_params(self) -> list[str]:
        params = []
        if 'export_text' in self.features:
            params.extend(['--text-output', f'{self.output.with_suffix(".txt")}', ])
        if 'export_json' in self.features:
            params.extend(['--json-output', f'{self.output.with_suffix(".json")}', ])
        if 'export_sarif' in self.features:
            params.extend(['--sarif-output', f'{self.output.with_suffix(".sarif")}', ])
        return params

    def __str__(self):
        return f'RunConfig(categories={self.categories}, languages={self.languages}, severities={self.severities}, features={self.features})'


if __name__ == "__main__":
    config = RunConfig.from_code('2Fn9bcbtctF')
    config = RunConfig.from_code('2Fn9bcbtcab')
    print(config)
    from semgrep_search.search import FilterConfig

    print(FilterConfig.from_config(config))
