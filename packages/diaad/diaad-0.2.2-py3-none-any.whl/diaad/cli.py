#!/usr/bin/env python3
"""
DIAAD Command-Line Interface
----------------------------
Entry point for the Digital Interface for Aphasiological Analysis of Discourse (DIAAD).
Delegates parser construction to main.build_arg_parser().
"""

from .main import main as main_core
from diaad.utils.auxiliary import build_arg_parser


def main():
    parser = build_arg_parser()
    args = parser.parse_args()
    main_core(args)


if __name__ == "__main__":
    main()
