import argparse
import os

from .download import download_gists
from .version import __version__


def main():
    parser = argparse.ArgumentParser(
        description="Download specified user's all gists at once",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog="Example: %(prog)s -u NecRaul -g",
    )
    parser.add_argument("-v", "--version", action="version", version=__version__)
    parser.add_argument(
        "-u",
        "--username",
        type=str,
        metavar="Username",
        help="Github username to download gists from.",
    )
    parser.add_argument(
        "-t",
        "--token",
        type=str,
        metavar="Token",
        help="Github public access token if you want to also download private gists.",
    )
    parser.add_argument(
        "-e",
        "--environment",
        action="store_true",
        help="Whether to use environment variables or not.",
    )
    parser.add_argument(
        "-g",
        "--git",
        action="store_true",
        help="Whether to download with git or not. False by default since it's "
        "dependent on whether or not git is downloaded (and your ssh/gpg key).",
    )

    args = parser.parse_args()

    if args.environment:
        username = os.getenv("GITHUB_USERNAME")
        token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
    else:
        username = args.username
        token = args.token

    git_check = args.git

    if not username:
        print("Pass your Github username with -u.")
    else:
        download_gists(username, token, git_check)
