# Semgrep-search

Did you ever want to search for semgrep rules from the [registry](https://semgrep.dev/r) and test your codebase against rules from the all search results?
`semgrep-search` allows you to search for languages, categories and severities and outputs a single YAML file that you can use with semgrep.

The database powering `semgrep-search` is automatically built continuously and published to ghcr.io through
[oras](https://github.com/oras-project) via [this project](https://github.com/hnzlmnn/semgrep-search-db).

## Installation

The easiest installation method is by using pip or pipx

For example using pip, `semgrep-search` can be installed by executing `pip install semgrep-search`

## Usage

### Creating rulesets

For example to search for all rules that test `csharp` code and are categorized as `security`-relevant run:

`sgs -l csharp -c security`

By default, `semgrep-search` will create a file `rules.yaml` in your current working directory.
Using `-O` you can specify a different path instead.
If the provided filename is `-`, `semgrep-search` write to STDOUT.

### Updating rules

If `semgrep-search` does not find the database locally, the database will automatically be downloaded when the tool runs.
However, from time to time, there might be new rules added to the registry.
To update the rules, run `semregp-search` with `--update`, shorthand `-u`,
and the current state of the registry will be downloaded before searching for any rules.

### Using the ruleset with semgrep

Use the ruleset with semgrep as follows `semgrep -c rules.yaml src/`

## Known issues

### The tool found more rules than the website

It appears as if semgrep.dev renamed `cs` (`C#` in the YAML files) to `csharp`,
however some old rules seem to exist as duplicates prefixed with `cs` however their web search filters these out.
I'm not quite sure why the JSON export still contains these and which other languages have been renamed in the past.

During database generation, languages will be normalized according to the
[table of languages](https://semgrep.dev/docs/writing-rules/rule-syntax/#language-extensions-and-languages-key-values)
from the Semgrep documentation.

### The registry shows more rules when filtering for a language

There seems to be at least one language (C#) that is being used with two different names.
Therefore, `semgrep-search` contains a list of programming language aliases that the semgrep registry allows.
If you happen to be missing a rule, please check the language specified in the rule or open a ticket with details about the missing rule.