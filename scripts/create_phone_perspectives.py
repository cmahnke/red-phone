import os
import json
import argparse
import re
import collections
import logging
import shutil

mp3_dir = "mp3"

def process_files(input_source):
    file_list = []
    processed_files = {}

    if isinstance(input_source, list):
        file_list = input_source
    elif isinstance(input_source, str):
        if os.path.isfile(input_source) and input_source.lower().endswith('.json'):
            try:
                with open(input_source, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        file_list = data
                    else:
                        logger.warning(f"JSON file '{input_source}' does not contain a list.")
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON format in '{input_source}'.")
            except FileNotFoundError:
                logger.error(f"JSON file '{input_source}' not found.")
        elif os.path.isdir(input_source):
            try:
                for filename in os.listdir(input_source):
                    if os.path.isfile(os.path.join(input_source, filename)):
                        file_list.append(filename)
            except OSError as e:
                logger.error(f"Error accessing directory '{input_source}': {e}")
        else:
            logger.error(f"Invalid input string. Must be a path to a JSON file or a directory: '{input_source}'")
    else:
        logger.error("Invalid input type. Must be a list, a JSON file path, or a directory path.")
        return {}

    pattern = re.compile(r"P_(\d+)-(\d+)_((\d{4}-\d{2}-\d{2}[a-z]?)|EXT)_(.+)_v(\d{4}-\d{2}-\d{2}[a-z]?)\.(mp3|MP3)$")
    # Regex pattern to capture the components:
    # 1. P_
    # 2. (XX-Y) - The number part we need to transform
    # 3. (_YYYY-MM-DDx) - The first date part to remove
    # 4. (_TITLE) - The title part to keep
    # 5. (_vYYYY-MM-DDx) - The version date part to remove
    # 6. (.ext) - The file extension to keep
    # The 'b' after the first date and 'e' after the second are optional letters,
    # so we use [a-z]? to allow for them.
    # The title part is flexible: it captures anything until '_v' or the extension.

    for filename in file_list:
        base_filename = os.path.basename(filename)
        match = pattern.match(base_filename)

        if match:
            first_num_part = match.group(1)
            second_num_part = match.group(2)
            title_part = match.group(5)
            extension = match.group(7)

            combined_num = first_num_part + second_num_part
            transformed_prefix = f"{int(combined_num):04d}"

            new_filename = f"{transformed_prefix}_{title_part}.{extension}"
            processed_files[base_filename] = new_filename
        else:
            logger.warning(f"Filename '{base_filename}' does not match the expected pattern. Skipping transformation.")
            #processed_files[base_filename] = base_filename

    return collections.OrderedDict(sorted(processed_files.items()))

if __name__ == "__main__":
    logger = logging.getLogger('Renamer')

    parser = argparse.ArgumentParser(
        description="Process audio file names to transform prefixes and remove specific date/version segments."
    )
    parser.add_argument(
        "-f", "--files",
        nargs='*',
        help="A list of file names separated by spaces."
    )
    parser.add_argument(
        "-j", "--json",
        help="Path to a JSON file containing a list of file names."
    )
    parser.add_argument(
        "-d", "--directory",
        help="Path to a directory to scan for files."
    )

    parser.add_argument(
        "-o", "--output",
        help=f"Path to copy files to."
    )

    parser.add_argument(
        "-p", "--print",
        action="store_true",
        help="Print mapping"
    )

    parser.add_argument(
        "-c", "--copy",
        action="store_true",
        help="Copy files"
    )

    args = parser.parse_args()

    input_data = None

    if args.files:
        input_data = args.files
        input_path = "./"
    elif args.json:
        input_data = args.json
        input_path = "./"
    elif args.directory:
        input_data = args.directory
        input_path = args.directory
    else:
        parser.print_help()
        exit(1)

    if args.output:
        output_path = os.path.join(args.output, mp3_dir)
        os.makedirs(output_path, exist_ok=True)
    else:
        output_path = "./"

    if args.copy:
        copy = True


    if input_data:
        result = process_files(input_data)       
        if result:
            for original, modified in result.items():
                target = os.path.join(output_path, modified)
                if args.print:
                    print(f"mv {original} {target}")
                if args.copy and args.output:
                    shutil.copyfile(os.path.join(input_path, original), target)
            
        else:
            print("No files processed or found matching the criteria.")

