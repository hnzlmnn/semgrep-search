# Semgrep-search

Did you ever want to search for semgrep rules from the [registry](https://semgrep.dev/r) and test your codebase against rules from the all search results?
`semgrep-search` allows you to search for languages, categories and severities and outputs a single YAML file that you can use with semgrep.

The database powering `semgrep-search` is automatically built continuously and published to ghcr.io through
[oras](https://github.com/oras-project) via [this project](https://github.com/hnzlmnn/semgrep-search-db).

Since version v1.1.2 there is also a web ui to inspect rules, create custom collections and generate run configurations: https://semgrep.cybaer.ninja/

## Installation

The easiest installation method is by using pip or pipx

For example, using pip, `semgrep-search` can be installed by executing `pip install semgrep-search`

## Usage

An alias for `semgrep-search` is automatically installed as `sgs`.

### Running semgrep

Since version v1.1.2 it is possible to directly run semgrep using `semgrep-search` in one step.

`semgrep-search run` takes the same arguments as `search`

```aiignore
usage: semgrep-search run [-h] [--language LANGUAGE] [--category {best-practice,correctness,maintainability,performance,portability,security}] [--severity {ERROR,INFO,WARNING}] [--origin ORIGIN] [--include-empty] [-R [RULES]] [-C [CONFIG]] [--binary BINARY] [--keep-rules-file] [--update] [-v]
                          [--database DATABASE] [--text | --no-text] [--json] [--sarif] [--all] [--output OUTPUT] [--force]
                          [TARGET]

positional arguments:
  TARGET                The target to run semgrep against (if none is provided uses working directory

options:
  -h, --help            show this help message and exit
  --language LANGUAGE, -l LANGUAGE
                        The language(s) to filter for. Separate multiple languages with comma or providing this argument multiple times
  --category {best-practice,correctness,maintainability,performance,portability,security}, -c {best-practice,correctness,maintainability,performance,portability,security}
                        The category(/ies) to filter for. Specify multiple categories by providing this argument multiple times
  --severity {ERROR,INFO,WARNING}, -s {ERROR,INFO,WARNING}
                        The severity(/ies) to filter for. Specify multiple severities by providing this argument multiple times
  --origin ORIGIN, -o ORIGIN
                        The origin(s) to select rules from. Specify multiple origins by providing this argument multiple times or by separating them by comma
  --include-empty, -e   Include rules that do not specify a selected filter at all
  -R [RULES], --rules [RULES]
                        Pre-generated set of rules to run semgrep with
  -C [CONFIG], --config [CONFIG]
                        The run configuration string
  --binary BINARY, -b BINARY
                        Specify the path to the semgrep binary (defaults to searching for "semgrep" in PATH)
  --keep-rules-file     If set, the temporary file containing the rules will not be deleted
  --update, -u          Force an update of the database
  -v, --verbose         Enable verbose logging
  --database DATABASE   Use a different location for the database
  --text, --no-text     Output a text file
  --json                Output a JSON file
  --sarif               Output a Sarif file
  --all                 Output all available file formats
  --output OUTPUT, -O OUTPUT
                        Output base filename (use - for stdout)
  --force, -f           If set, existing output file(s) will be overwritten
```

### Inspecting the database

To view details about the database run `sgs inspect`.

### Creating rulesets

To search for all rules that test `csharp` code and are categorized as `security`-relevant run:

`sgs search -l csharp -c security`

By default, `semgrep-search` will create a file `rules.yaml` in your current working directory.
Using `-O` you can specify a different path instead.
If the provided filename is `-`, `semgrep-search` write to STDOUT.

### Updating rules

If `semgrep-search` does not find the database locally, the database will automatically be downloaded when the tool runs.
However, from time to time, there might be new rules added to the registry.
To update the rules, run `semregp-search` with `--update`, shorthand `-u`,
and the current state of the registry will be downloaded before searching for any rules.

## Known issues

### The tool found more rules than the website

It appears as if semgrep.dev renamed `cs` (`C#` in the YAML files) to `csharp`.
However, some old rules seem to exist as duplicates prefixed with `cs` and semgrep's web search filters these out.
I'm not quite sure why the JSON export still contains these and which other languages have been renamed in the past.

During database generation, languages will be normalized according to the
[table of languages](https://semgrep.dev/docs/writing-rules/rule-syntax/#language-extensions-and-languages-key-values)
from the Semgrep documentation.

### The registry shows more rules when filtering for a language

There seems to be at least one language (C#) that is being used with two different names.
Therefore, `semgrep-search` contains a list of programming language aliases that the semgrep registry allows.
If you happen to be missing a rule, please check the language specified in the rule or open a ticket with details about the missing rule.