"""
The main module of this package. The relative path is with respect to the
coguard cli project where it is integrated in.
"""

import argparse
from coverity_integration.src.coguard_coverity_translator import entrypoint

def main():
    """
    The main entrypoint where we are collecting parser arguments.
    """
    parser = argparse.ArgumentParser(
        description="The main entrypoint for CoGuard Coverity translator"
    )
    parser.add_argument(
        'folder_name',
        metavar='folder_name',
        type=str,
        default=".",
        nargs='?',
        help=("The folder where the results are located.")
    )
    args = parser.parse_args()
    entrypoint(args)

if __name__ == '__main__':
    main()
