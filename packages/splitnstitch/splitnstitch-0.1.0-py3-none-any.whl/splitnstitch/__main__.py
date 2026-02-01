import sys
import argparse

import importlib.metadata
from splitnstitch.splitnstitch import main as _interactive_main

try:
    __version__ = importlib.metadata.version('splitnstitch')
except importlib.metadata.PackageNotFoundError:
    __version__ = "Package not installed..."


def main(argv=None):
	"""Entry point for console script.

	Supports -?/--help and -v/--version. If no version flag is passed,
	runs the interactive `main()` from `splitnstitch.splitnstitch`.
	"""
	parser = argparse.ArgumentParser(add_help=False)
	parser.add_argument('-?', '--help', action='help', help='show this help message and exit')
	parser.add_argument('-v', '--version', action='store_true', help='show program version and exit')
	args, _rest = parser.parse_known_args(argv)

	if args.version:
		print(__version__)
		return 0

	# No version flag -> run interactive CLI
	try:
		_interactive_main()
	except SystemExit as e:
		return e.code if isinstance(e.code, int) else 0
	return 0


if __name__ == '__main__':
	raise SystemExit(main(sys.argv[1:]))
