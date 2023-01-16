<p align="center">
    <a href="https://github.com/ActionsToolbox/">
        <img src="https://cdn.wolfsoftware.com/assets/images/github/organisations/actionstoolbox/black-and-white-circle-256.png" alt="ActionsToolbox logo" />
    </a>
    <br />
    <a href="https://github.com/ActionsToolbox/get-language-versions-action/actions/workflows/cicd-pipeline-local.yml">
        <img src="https://img.shields.io/github/actions/workflow/status/ActionsToolbox/get-language-versions-action/cicd-pipeline-local.yml?branch=master&label=local%20pipeline&style=for-the-badge" alt="Github Build Status" /> <img
    </a>
    <a href="https://github.com/ActionsToolbox/get-language-versions-action/actions/workflows/cicd-pipeline-shared.yml">
        <img src="https://img.shields.io/github/actions/workflow/status/ActionsToolbox/get-language-versions-action/cicd-pipeline-shared.yml?branch=master&label=shared%20pipeline&style=for-the-badge" alt="Github Build Status" />
    </a>
    <br />
    <a href="https://github.com/ActionsToolbox/get-language-versions-action/blob/master/.github/CODE_OF_CONDUCT.md">
        <img src="https://img.shields.io/badge/Code%20of%20Conduct-blue?style=for-the-badge" />
    </a>
    <a href="https://github.com/ActionsToolbox/get-language-versions-action/blob/master/.github/CONTRIBUTING.md">
        <img src="https://img.shields.io/badge/Contributing-blue?style=for-the-badge" />
    </a>
    <a href="https://github.com/ActionsToolbox/get-language-versions-action/blob/master/.github/SECURITY.md">
        <img src="https://img.shields.io/badge/Report%20Security%20Concern-blue?style=for-the-badge" />
    </a>
    <a href="https://github.com/ActionsToolbox/get-language-versions-action/issues">
        <img src="https://img.shields.io/badge/Get%20Support-blue?style=for-the-badge" />
    </a>
</p>

## Overview

This action was inspired by [latest-python-versions](https://github.com/snok/latest-python-versions)

# Latest Language Version(s)

This action will fetch up-to-date data on the latest version(s) available on Github Actions for a given set of languages.

| Language      | GitHub Action                                           | Version Source                                                                                           |
| ------------- |:-------------------------------------------------------:| :-------------------------------------------------------------------------------------------------------:|
| Go            | [setup-go](https://github.com/actions/setup-go)         | [go-versions](https://raw.githubusercontent.com/actions/go-versions/main/versions-manifest.json)         |
| Node / NodeJS | [setup-node](https://github.com/actions/setup-node)     | [node-versions](https://raw.githubusercontent.com/actions/node-versions/main/versions-manifest.json)     |
| PHP           | [setup-php](https://github.com/shivammathur/setup-php)  | [php-versions](https://phpreleases.com/api/releases/)                                                    |
| Python        | [setup-python](https://github.com/actions/setup-python) | [python-versions](https://raw.githubusercontent.com/actions/python-versions/main/versions-manifest.json) |
| Ruby          | [setup-ruby](https://github.com/ruby/setup-ruby)        | [ruby-versions](https://raw.githubusercontent.com/ruby/setup-ruby/master/ruby-builder-versions.json)     |

If you're already running tests on multiple versions of a language, this action will allow you to replace your static
matrix definitions with dynamic ones. It will also allow you to define a specific version if you are running a single version of a language.

## Usage

To use the action, simply throw this into one of your workflows

```yaml
- uses: ActionsToolbox/get-latest-language-versions@master
  id: get-versions
  with:
    language: "python"
    min-version: 3.7           # not required - defaults to "EOL"
    max-version: 3.10          # not required - defaults to latest
    include-prereleases: true  # not required - defaults to false
    highest-only: true         # not required - defaults to false
```

The action produces an `output` that can be accessed using:

```python
${{ steps.get-versions.outputs.latest-versions }}
```

## All Parameters

| Parameters          | Required | Default  | Options                             |
| ------------------- |:--------:| -------- | ----------------------------------- |
| language            | Yes      |          | go, node, nodejs, php, python, ruby |
| min-version         | No       | "EOL"    | semver, EOL, ALL                    |
| max-version         | No       | "latest" | semver, latest                      |
| include-prereleases | No       | false    | false, true                         |
| highest-only        | No       | false    | false, true                         |

See examples below for recommended usage.

## Example

### Matrix Example

This example will return a list of versions of Python from 3.8 up to and including the latest pre-release version. This is then converted into a matrix using fromJson.

```yaml
name: Test

on: pull_request

jobs:
  linting:
    ...

  # Define the job to run before your matrix job
  get-versions:
    runs-on: ubuntu-latest
    outputs:
      version-matrix: ${{ steps.get-latest-versions.outputs.latest-versions }}
    steps:
    - uses: ActionsToolbox/get-language-versions-action@master
      id: get-language-versions
      with:
        language: "python"
        min-version: 3.8
        include-prereleases: true

  # Then use the output from the previous job in the matrix definition
  test:
    needs: [linting, get-versions]
    runs-on: ubuntu-latest
    strategy:
      matrix:
        version: ${{ fromJson(needs.get-versions.outputs.version-matrix) }}
    steps:
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.version }}
```

### Single Value Example

This example will return the highest non pre-release version of Python as a string which is then used in setup python for a single job.

```yaml
name: Test

on: pull_request

jobs:
  linting:
    ...

  # Define the job to run before your matrix job
  get-versions:
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.get-latest-versions.outputs.latest-versions }}
    steps:
    - uses: ActionsToolbox/get-language-versions-action@master
      id: get-language-versions
      with:
        language: "python"
        highest-only: true

  # Then use the output from the previous job in the matrix definition
  test:
    needs: [linting, get-versions]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ needs.get-versions.outputs.version }}
```


<br />
<p align="right"><a href="https://wolfsoftware.com/"><img src="https://img.shields.io/badge/Created%20by%20Wolf%20Software-blue?style=for-the-badge" /></a></p>
