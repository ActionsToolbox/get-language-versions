"""
Inspired by: https://github.com/snok/latest-python-versions.

This action allows you to get either the single latest version or a list of versions which can be used
as a matrix in a github action.

It currently supports the following languages:

1. Go
2. Node / NodeJS
3. Perl
4. PHP
5. Python
6. Ruby
7. Terraform
"""
import datetime
import json
import os
import sys

import requests
from packaging import version as semver

from bs4 import BeautifulSoup

# pylint: disable=too-many-arguments

REQUESTS_TIMEOUT: int = 5
MAX_VERSION: semver.Version = semver.parse('99999')
MIN_VERSION: semver.Version = semver.parse('0')

URLS: dict[str, dict[str, str]] = {
    "go": {
        "releases_url": 'https://github.com/actions/go-versions/releases/latest/',
        "head_branch": 'main',
        "versions_url": 'https://raw.githubusercontent.com/actions/go-versions/LATEST_TAG/versions-manifest.json',
        "eol_url": 'https://endoflife.date/api/go.json'
    },
    "node": {
        "releases_url": 'https://github.com/actions/node-versions/releases/latest/',
        "head_branch": 'main',
        "versions_url": 'https://raw.githubusercontent.com/actions/node-versions/LATEST_TAG/versions-manifest.json',
        "eol_url": 'https://endoflife.date/api/nodejs.json'
    },
    "nodejs": {
        "releases_url": 'https://github.com/actions/node-versions/releases/latest/',
        "head_branch": 'main',
        "versions_url": 'https://raw.githubusercontent.com/actions/node-versions/LATEST_TAG/versions-manifest.json',
        "eol_url": 'https://endoflife.date/api/nodejs.json'
    },
    "perl": {
        "releases_url": 'https://github.com/shogo82148/actions-setup-perl/releases/latest/',
        "head_branch": 'main',
        "versions_url": 'https://raw.githubusercontent.com/shogo82148/actions-setup-perl/LATEST_TAG/versions/linux.json',
        "eol_url": 'https://endoflife.date/api/perl.json'
    },
    "php": {
        "versions_url": 'https://phpreleases.com/api/releases/',
        "eol_url": 'https://endoflife.date/api/php.json'
    },
    "python": {
        "releases_url": 'https://github.com/actions/python-versions/releases/latest/',
        "head_branch": 'main',
        "versions_url": 'https://raw.githubusercontent.com/actions/python-versions/LATEST_TAG/versions-manifest.json',
        "eol_url": 'https://endoflife.date/api/python.json'
    },
    "ruby": {
        "releases_url": 'https://github.com/ruby/setup-ruby/releases/latest/',
        "head_branch": 'master',
        "versions_url": 'https://raw.githubusercontent.com/ruby/setup-ruby/LATEST_TAG/ruby-builder-versions.json',
        "eol_url": 'https://endoflife.date/api/ruby.json'
    },
    "terraform": {
        "versions_url": 'https://releases.hashicorp.com/terraform/',
        "eol_url": 'https://endoflife.date/api/terraform.json'
    }
}


def strtobool(bool_str: str) -> bool:
    """
    Convert a string to a boolean.

    distutils.util.strtobool is deprecated and not available for python 3.10+ so I had to write my own.

    Arguments:
        bool_str (str) -- The string to convert into a boolean.

    Returns:
        bool -- The resultant boolean value.
    """
    if bool_str.lower() in ["true", "1"]:
        return True
    return False


def get_minimum_version_from_oel(language: str) -> str:
    """
    Get the minimum version from the EOL url.

    The default value for min-version is "EOL" so we need to have a way to get the min-version from the
    EOL url.

    Arguments:
        language (str) -- The supported language to use to locate the correct EOL url.

    Returns:
        str -- The minimum "supported" version.
    """
    versions_url: str = URLS[language]["eol_url"]
    min_version: str = MAX_VERSION

    for release in requests.get(versions_url, timeout=REQUESTS_TIMEOUT).json():
        try:
            semver.Version(release['cycle'])
        except semver.InvalidVersion:
            continue

        if release['eol'] is True:
            continue

        if release['eol'] is False:
            if semver.parse(release['cycle']) < min_version:
                min_version: str = semver.parse(release['cycle'])
            continue

        if datetime.date.today() < datetime.date.fromisoformat(release['eol']):
            min_version = semver.parse(release['cycle'])

    return min_version


def get_minimum_version(min_version: str, language: str) -> str:
    """
    Get the min-version.

    There are multiple ways to define the min-version we want to use, this is a simple wrapper to correctly set the right version.

    Arguments:
        min_version (str) -- The min-version as supplied to the action by the user (or the default is non is supplied)
        language (str) -- The supported language to.

    Returns:
        str -- The minimum version for the supplied language.
    """
    if min_version.upper() == 'EOL':
        min_version: str = get_minimum_version_from_oel(language)
    elif min_version.upper() == 'ALL':
        min_version = MIN_VERSION
    else:
        min_version = semver.parse(min_version)
    return min_version


def get_latest_tag(releases_url: str) -> str:
    """
    Define a summary.

    This is the extended summary from the template and needs to be replaced.

    Arguments:
        releases_url (str) -- _description_

    Returns:
        str -- _description_
    """
    response: requests.models.Response = requests.get(releases_url, timeout=10)
    version: str = response.url.split('/')[-1]

    return version


def get_stable_versions(language: str, use_head: bool, return_json: bool = True) -> list:
    """
    Get a list of stable versions.

    For a given language, locate the current stable (supported) versions.

    Arguments:
        language (str) -- The supported language to use.

    Returns:
        list -- The list of stable (supported) versions available.
    """
    versions_url: str = URLS[language]["versions_url"]

    if use_head is True:
        head_branch: str = URLS[language]["head_branch"]
        versions_url = versions_url.replace('LATEST_TAG', head_branch)
    elif "releases_url" in URLS[language]:
        latest_tag: str = get_latest_tag(URLS[language]["releases_url"])
        versions_url = versions_url.replace('LATEST_TAG', latest_tag)

    if return_json is True:
        return requests.get(versions_url, timeout=REQUESTS_TIMEOUT).json()
    return requests.get(versions_url, timeout=REQUESTS_TIMEOUT).text


def compare_min_max_value(versions_dict: dict, version: str, min_version: str, max_version: str) -> dict:
    """
    Compare version against min and max.

    Compare the current version against the min and max to see if it within the range we want.

    Arguments:
        versions_dict (dict) -- The dictionary of valid versions.
        version (str) -- The current version we are comparing.
        min_version (str) -- The minimum defined version.
        max_version (str) -- The maximum defined version.

    Returns:
        dict -- The updated versions dictionary.
    """
    major_minor: semver.Version = semver.parse('.'.join(version.split('.')[:2]))

    if min_version <= major_minor <= max_version:
        if major_minor in versions_dict:
            if semver.parse(versions_dict[major_minor]) < semver.parse(version):
                versions_dict[major_minor] = version
        else:
            versions_dict[major_minor] = version

    return versions_dict


def process_versions(stable_versions: list, min_version: str, max_version: str, include_prereleases: bool, remove_patch_version: bool) -> list:
    """
    Process the list of versions.

    Process the list of versions, and ensure they are within the min-version and max-version.

    Arguments:
        stable_versions (list) -- The list of stable versions.
        min_version (str) -- The minimum identified version.
        max_version (str) -- The maximum identified version.
        parsed_include_prereleases (bool) -- Should we include pre-releases?

    Returns:
        list -- The complete list of versions within our defined bounds.
    """
    versions_dict: dict = {}

    for version in stable_versions:
        try:
            semver.Version(version)
        except semver.InvalidVersion:
            continue

        if not include_prereleases and semver.parse(version).is_prerelease:
            continue

        if remove_patch_version:
            version: str = '.'.join(version.split('.')[:2])

        versions_dict = compare_min_max_value(versions_dict, version, min_version, max_version)

    versions: list = list(versions_dict.values())
    versions = sorted(versions, key=lambda x: [int(i) if i.isdigit() else i for i in x.split('.')])
    return versions


def get_versions(stable_versions: dict) -> list:
    """
    Get versions from returned dataset.

    Different version urls return the version data in different formats, this handles the data for Go, Nodejs and Python.

    Arguments:
        stable_versions (dict) -- The dataset returned from the versions-url.

    Returns:
        list -- A list containing JUST the version numbers.
    """
    versions: list = []

    for version_object in stable_versions:
        version: str = version_object['version']

        try:
            if semver.Version(version):
                versions.append(version)
        except semver.InvalidVersion:
            continue

    return versions


def get_perl_versions(stable_versions: dict) -> list:
    """
    Get versions from returned dataset.

    Different version urls return the version data in different formats, this handles the data for Ruby only.

    Arguments:
        stable_versions (dict) -- The dataset returned from the versions-url.

    Returns:
        list -- A list containing JUST the version numbers.
    """
    versions: list = []

    for version in stable_versions:
        try:
            if semver.Version(version):
                versions.append(version)
        except semver.InvalidVersion:
            continue

    return versions


def get_php_versions(stable_versions: dict) -> list:
    """
    Get versions from returned dataset.

    Different version urls return the version data in different formats, this handles the data for PHP only.

    Arguments:
        stable_versions (dict) -- The dataset returned from the versions-url.

    Returns:
        list -- A list containing JUST the version numbers.
    """
    versions: list = []

    for version_object in stable_versions:
        version: str = f"{version_object['major']}.{version_object['minor']}.{version_object['release']}"

        try:
            if semver.Version(version):
                versions.append(version)
        except semver.InvalidVersion:
            continue

    return versions


def get_ruby_versions(stable_versions: dict) -> list:
    """
    Get versions from returned dataset.

    Different version urls return the version data in different formats, this handles the data for Ruby only.

    Arguments:
        stable_versions (dict) -- The dataset returned from the versions-url.

    Returns:
        list -- A list containing JUST the version numbers.
    """
    versions: list = []

    for version in stable_versions["ruby"]:
        try:
            if semver.Version(version):
                versions.append(version)
        except semver.InvalidVersion:
            continue

    return versions


def get_terraform_versions(stable_versions: dict) -> list:
    """
    Get versions from returned dataset.

    Different version urls return the version data in different formats, this handles the data for Terraform only.

    Arguments:
        stable_versions (dict) -- The dataset returned from the versions-url.

    Returns:
        list -- A list containing JUST the version numbers.
    """
    versions: list = []

    soup: BeautifulSoup = BeautifulSoup(stable_versions, features="html.parser")
    for link in soup.findAll('a'):
        version: str = link['href'].replace('/terraform/', '').replace('/', '')
        try:
            semver.Version(version)
        except semver.InvalidVersion:
            continue
        else:
            versions.append(version)

    return versions


def output_version_details(versions: list | str) -> None:
    """
    Output the version information.

    Output the version(s) that match the user criteria.

    Arguments:
        versions (list | str) -- The version(s) that match the user criteria.
    """
    if 'GITHUB_ENV' in os.environ:
        with open(os.environ['GITHUB_ENV'], 'a', encoding="UTF-8") as file:
            file.write(f'LATEST_VERSIONS={versions}')

    if 'GITHUB_OUTPUT' in os.environ:
        with open(os.environ['GITHUB_OUTPUT'], 'a', encoding="UTF-8") as file:
            file.write(f'latest-versions={versions}')

    print(versions)


def main(language: str,
         min_version: str = 'EOL',
         max_version: str = 'LATEST',
         include_prereleases: str = 'false',
         highest_only: str = 'false',
         remove_patch_version: str = 'false',
         use_head: str = 'false',
         max_versions: int = 0) -> None:
    """
    Handle input from Docker container.

    This is the main function and what is called when the container is run, it takes all of the input from the GitHub Action and processes it to locate
    the correct requested version information.

    Arguments:
        language (str) -- The language to find the versions for.

    Keyword Arguments:
        min_version (str) -- The minimum version to use (default: 'EOL')
        max_version (str) -- The maximum version to use (default: 'LATEST')
        include_prereleases (str) -- Should we include pre-release versions? (default: 'false')
        highest_only (str) -- Should we return only the highest version instead of all? (default: 'false')
        remove_patch_version (str) -- Should we return only the major.minor version instead of the full version? (default: 'false')
        use_head (str) - Should we use the latest commit to master instead of the latest release? (default: 'false')
    """
    version_json: list = []

    if language.lower() not in URLS:
        print(f"{language} is not a valid options. Valid options are: go, node, nodejs, php, python or ruby")
        sys.exit(1)

    min_version: str = get_minimum_version(min_version, language)
    max_version: str = semver.parse(max_version) if max_version.upper() != 'LATEST' else MAX_VERSION
    include_prereleases: bool = strtobool(include_prereleases)
    highest_only: bool = strtobool(highest_only)
    remove_patch_version: bool = strtobool(remove_patch_version)
    use_head: bool = strtobool(use_head)
    max_versions: int = int(max_versions)

    if remove_patch_version and include_prereleases:
        print("You cannot combine include_prereleases with remove_patch")
        sys.exit(1)

    if language.upper() == "TERRAFORM":
        stable_versions: list = get_stable_versions(language, use_head, False)
    else:
        stable_versions: list = get_stable_versions(language, use_head)

    if language.upper() == "PERL":
        versions: list = get_perl_versions(stable_versions)
    elif language.upper() == "PHP":
        versions: list = get_php_versions(stable_versions)
    elif language.upper() == "RUBY":
        versions = get_ruby_versions(stable_versions)
    elif language.upper() == "TERRAFORM":
        versions = get_terraform_versions(stable_versions)
    else:
        versions = get_versions(stable_versions)

    versions = process_versions(versions, min_version, max_version, include_prereleases, remove_patch_version)

    if highest_only:
        version_json = versions[-1]
    else:
        if max_versions > 0:
            versions = versions[-max_versions:]

        version_json = json.dumps(versions)

    output_version_details(version_json)


if __name__ == '__main__':
    main(*sys.argv[1:])
