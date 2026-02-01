from .transformer import transpile_file

from argparse import ArgumentParser
from pathlib import Path


def main():
    parser = ArgumentParser(description='ArchiCat CLI')
    parser.add_argument('input',help='input file')
    parser.add_argument('-o','--output',help='output file')
    args = parser.parse_args()
    transpile_file(
        args.input,
        args.output or (Path(args.input).parent / (Path(args.input).stem + '.sb3'))
    )

if __name__ == '__main__':
    main()