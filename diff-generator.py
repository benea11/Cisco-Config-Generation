import diffios
import time
import argparse


def main():
    parser = argparse.ArgumentParser(
        description='This script is used for creating the differential between configurations')
    parser.add_argument('--new', metavar='new', help='Our configuration, the one we have staged and will install')
    parser.add_argument('--old', metavar='old', help='Their configuration, the one we replace')
    parser.add_argument('--ignore', metavar='ignore', help='specify the file containing commands to ignore')
    args = parser.parse_args()
    baseline = args.new
    comparison = args.old
    ignore = args.ignore

    diff = diffios.Compare(baseline, comparison, ignore)
    with open('results.txt', 'w') as out_file:
        out_file.write(diff.pprint_additional())


if __name__ == "__main__":
    start_time = time.time()
    main()
    run_time = time.time() - start_time
    print("\n** Configuration Generated")
    print("** Time to run: %s sec" % round(run_time, 3))