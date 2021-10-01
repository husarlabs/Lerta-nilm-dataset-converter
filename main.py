import argparse

from convert_dataset import convert_dataset


def parse_args() -> str:
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dir-path', type=str, required=True)
    args = parser.parse_args()
    params = vars(args)

    return params.get('dir_path')


def main() -> None:
    dir_path = parse_args()
    convert_dataset(dir_path)


if __name__ == '__main__':
    main()
