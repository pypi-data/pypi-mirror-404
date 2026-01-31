import argparse
import csv
import json
import sys

from graffiti_lookup.client import GraffitiLookup

SUPPORTED_FILE_TYPES = ("csv", "json")

parser = argparse.ArgumentParser(description="Fetch NYC Graffiti Service Request")
parser.add_argument(
    "-i",
    "--id",
    help="graffiti service request id",
)
parser.add_argument(
    "-L", "--ids", help="Comma separated list of graffiti service request ids"
)
parser.add_argument(
    "-f",
    "--file-path",
    help="The output file path for the requested graffiti service request records",
)
parser.add_argument(
    "-m",
    "--merge-file",
    action="store_true",
    help="Merge graffiti request records with existing file",
)
parser.add_argument(
    "-t", "--file-type", choices=SUPPORTED_FILE_TYPES, help="The output file type"
)

# Parse empty args at import time so pytest (and other importers) don't consume CLI argv.
# When executing as a script we parse the real command-line args in the __main__ block.
args = parser.parse_args([])


def read_file(file_path, file_type, fieldnames):
    try:
        with open(file_path, "r") as file:
            if file_type == "json":
                return json.loads(file.read())
            elif file_type == "csv":
                csv_reader = csv.DictReader(file, fieldnames=fieldnames)
                return [row for row in csv_reader][1:]
            else:
                sys.stderr.write(
                    f"Unsupported file-type {file_type} not in {SUPPORTED_FILE_TYPES}"
                )
    except FileNotFoundError:
        pass

    return []


def write_file(file_path, file_type, result, fieldnames):
    if file_type not in SUPPORTED_FILE_TYPES:
        sys.stderr.write(
            f"Unsupported file-type {file_type} not in {SUPPORTED_FILE_TYPES}"
        )
        return

    with open(file_path, "w") as file:
        if file_type == "json":
            file.write(json.dumps(result, indent=4))
        elif file_type == "csv":
            csv_writer = csv.DictWriter(file, fieldnames=fieldnames)
            csv_writer.writeheader()
            if isinstance(result, list):
                csv_writer.writerows(result)
            else:
                csv_writer.writerow(result)


async def main(cli_args=None):
    if cli_args is None:
        cli_args = args

    graffiti_lookup_service = GraffitiLookup()
    result = None
    file_path = cli_args.file_path
    file_type = cli_args.file_type or (file_path and file_path.split(".")[-1].lower())

    if cli_args.id:
        result = await graffiti_lookup_service.get_status_by_id(cli_args.id)

    if cli_args.ids:
        service_ids = cli_args.ids.replace(" ", "").split(",")
        result = await graffiti_lookup_service.get_statuses_by_id(service_ids)

    try:
        fieldnames = result[0].keys() if cli_args.ids else result.keys()
    except (IndexError, AttributeError):
        fieldnames = []

    if not file_path:
        sys.stdout.write(json.dumps(result))
    else:
        if cli_args.merge_file:
            file_results = read_file(file_path, file_type, fieldnames)
            file_result_map = {
                row.get(GraffitiLookup.ID_FIELD): row for row in file_results
            }
            result_map = {row.get(GraffitiLookup.ID_FIELD): row for row in result}
            all_results = {**file_result_map, **result_map}
            result = list(all_results.values())

        write_file(file_path, file_type, result, fieldnames)


def cli_main():
    import asyncio

    cli_args = parser.parse_args()
    asyncio.run(main(cli_args))


if __name__ == "__main__":
    cli_main()
