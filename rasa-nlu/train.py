#!/usr/bin/env python

from argparse import ArgumentParser
import json
import os
from pathlib import Path


class EnvironmentVariableNotDefinedException(Exception):
    pass


class CommandFailedError(Exception):
    pass


class AbstractExecutor:
    def execute(self, command):
        raise NotImplementedError()

    def on_done(self):
        pass

    def train(self, url):
        self.execute(
            f"curl --fail --location --request POST {url} --header 'Content-Type: application/json' --data-binary '@./payload.json' -OJ -vv"
        )


class Executor(AbstractExecutor):
    def execute(self, command):
        exit_code = os.system(command)
        if exit_code != 0:
            raise CommandFailedError(
                f"Expected '{command}' to succeed but it failed with code {exit_code}"
            )


class Printer(AbstractExecutor):
    def __init__(self):
        self._commands = []

    def execute(self, command):
        self._commands.append(command)

    def on_done(self):
        print(" && ".join(self._commands))


def getenv(key, default=None):
    value = os.getenv(key, default)
    if value:
        return value
    if default is not None:
        return default
    raise EnvironmentVariableNotDefinedException(
        "Expected environment variable '{}' to be defined but it wasn't".
        format(key))


def parse_args():
    parser = ArgumentParser()
    parser.add_argument("-t",
                        "--training-data",
                        default="training-data.md",
                        help="file that contains markdown training data")
    parser.add_argument("-c",
                        "--config",
                        default="config.yml",
                        help="file that contains YAML config")
    parser.add_argument("-o",
                        "--output",
                        default="payload.json",
                        help="file to write JSON payload")
    parser.add_argument(
        "--print-commands",
        action="store_true",
        help="print subcommands instead of executing them, allowing the hosting shell to execute them instead"
    )  # yapf: disable
    parser.add_argument("-u", "--url", help="URL to Rasa server")
    return parser.parse_args()


def construct_payload(training_data_path, config_path, output_path):
    def read(path):
        path = Path(path)
        with path.open() as fd:
            return fd.read()

    def construct():
        training_data = read(training_data_path)
        config = read(config_path)
        return {
            "config": config,
            "nlu": training_data,
        }

    def write(payload):
        with Path(output_path).open(mode="w") as file_:
            json.dump(payload,
                      file_,
                      sort_keys=True,
                      indent=4,
                      separators=(',', ': '))

    payload = construct()
    write(payload)


def main():
    args = parse_args()
    executor = Printer() if args.print_commands else Executor()
    construct_payload(args.training_data, args.config, args.output)
    executor.train(args.url)
    executor.on_done()


if __name__ == "__main__":
    main()
