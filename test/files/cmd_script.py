import argparse


def main():
    vrs_num = '1.0'
    parser = argparse.ArgumentParser(
        description='callable cmd testing script',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        usage=argparse.SUPPRESS
    )
    parser.add_argument(
        '-v', '--version',
        action='version',
        version='%(prog)s ' + vrs_num
    )
    parser.add_argument(
        '-a', '--alpha',
        help='Parameter 1',
        required=True
    )
    parser.add_argument(
        '-b', '--beta',
        help='Parameter 2'
    )
    args = parser.parse_args()


if __name__ == '__main__':
    main()
