from __future__ import annotations

import importlib
import importlib.util
import json
import signal
import traceback
from collections import deque
from pathlib import Path
from typing import Any

import click
import yaml
from click import echo
from typing_extensions import Iterable

# from fixmate.common.client.fixed import PatchedClient
# from fixmate.common.constants import PROMPT_TEMPLATE_FILE_KEY
# from fixmate.logger import init_cli_logger, logger


from fixmate.common.client.fixed import PatchedClient
from fixmate.common.constants import PROMPT_TEMPLATE_FILE_KEY
from fixmate.logger import init_cli_logger, logger

_DATA_FORMAT_MAPPING = {
    "yaml": yaml.dump,
    "json": json.dumps,
}

_CONFIG_NAME = "config.yml"
_PROMPT_NAME = "prompt.json"
_PATCHFLOW_MODULE_NAME = "fixmate.fixflows"


def _get_fixflow_names(base_path: Path | str | None) -> Iterable[str]:
    names = []
    if base_path is None:
        return names

    base_path = Path(base_path)
    if not base_path.is_dir():
        return names

    for path in base_path.iterdir():
        if path.is_dir() and (path / f"{path.name}.py").is_file():
            names.append(path.name)
    return sorted(names)


def list_option_callback(ctx: click.Context, param: click.Parameter, value: str | None) -> None:
    if not value or ctx.resilient_parsing:
        return

    fixflows = []
    default_path = Path(__file__).parent / "fixflows"
    fixflows.extend(_get_fixflow_names(default_path))

    config_path = ctx.params.get("config")
    fixflows.extend(_get_fixflow_names(config_path))

    echo("\n".join(fixflows), color=ctx.color)
    ctx.exit()


def find_fixflow(possible_module_paths: Iterable[str], fixflow: str) -> Any | None:
    for module_path in possible_module_paths:
        try:
            print('kdndssd', module_path)
            spec = importlib.util.spec_from_file_location("custom_module", module_path)
            print("kjskjdsd", spec)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            logger.info(f'Patchflow `{fixflow}` loaded from "{module_path}"')
            return getattr(module, fixflow)
        except AttributeError:
            logger.debug(f"Patchflow {fixflow} not found in {module_path}")
        except Exception:
            logger.debug(f"Patchflow {fixflow} not found as a file/directory in {module_path}")

        try:
            module = importlib.import_module(module_path)
            logger.info(f"Patchflow {fixflow} loaded from {module_path}")
            return getattr(module, fixflow)
        except ModuleNotFoundError:
            logger.debug(f"Patchflow {fixflow} not found as a module in {module_path}")
        except AttributeError:
            logger.debug(f"Patchflow {fixflow} not found in {module_path}")

    return None


def setup_cli():
    def sigint_handler(signum, frame):
        logger.info("Received SIGINT, exiting")
        exit(1)

    signal.signal(signal.SIGINT, sigint_handler)


@click.command(
    context_settings=dict(
        ignore_unknown_options=True,
    )
)
@click.version_option(message="%(version)s", package_name="fixmate-cli")
@click.help_option("-h", "--help")
@click.option(
    "--config",
    is_eager=True,
    type=click.Path(exists=True, dir_okay=True, resolve_path=True, file_okay=True),
    help="Path to the configurations folder, see https://github.com/fixed-codes/fixmate-configs for examples.",
)
@click.option(
    "-l",
    "--list",
    is_flag=True,
    expose_value=False,
    callback=list_option_callback,
    help="Show a list of available fixflows, see https://docs.fixed.codes/fixflows/fixflows for details.",
)
@click.option(
    "--log",
    hidden=True,
    default="INFO",
    type=click.Choice(
        [
            "CRITICAL",
            "FATAL",
            "ERROR",
            "WARNING",
            "WARN",
            "INFO",
            "DEBUG",
            "TRACE",
        ],
        case_sensitive=False,
    ),
    is_eager=True,
    callback=lambda x, y, z: init_cli_logger(z),
)
@click.argument("fixflow", nargs=1, required=True)
@click.argument("opts", nargs=-1, type=click.UNPROCESSED, required=False)
@click.option(
    "--output",
    type=click.Path(exists=False, resolve_path=True, writable=True),
    help="Path to the output file which contains the state after the fixflow finishes.",
)
@click.option(
    "data_format", "--format", type=click.Choice(["yaml", "json"]), default="json", help="Format of the output file."
)
@click.option("fixed_api_key", "--fixed_api_key", help="API key to use with the fixed.codes service.")
@click.option("disable_telemetry", "--disable_telemetry", is_flag=True, help="Disable telemetry.", default=False)
def cli(
    log: str,
    fixflow: str,
    opts: list[str],
    config: str | None,
    output: str | None,
    data_format: str,
    fixed_api_key: str | None,
    disable_telemetry: bool,
):
    setup_cli()
    print(log, fixflow,
    opts,
    config,
    output,
    data_format,
    fixed_api_key,
    disable_telemetry)
    if "::" in fixflow:
        module_path, _, fixflow_name = fixflow.partition("::")
    else:
        fixflow_name = fixflow
        module_path = _PATCHFLOW_MODULE_NAME

    possbile_module_paths = deque((module_path,))

    with logger.panel("Initializing Fixmate CLI"):
        inputs = {}
        if fixed_api_key is not None:
            inputs["fixed_api_key"] = fixed_api_key

        if config is not None:
            logger.info(f"Using given config value: {config}")
            config_path = Path(config)
            if config_path.is_file():
                inputs = yaml.safe_load(config_path.read_text()) or {}
                logger.info(f"Input values loaded from {config}")
            elif config_path.is_dir():
                fixmate_path = config_path / fixflow_name

                fixmate_python_path = fixmate_path / f"{fixflow_name}.py"
                if fixmate_python_path.is_file():
                    possbile_module_paths.appendleft(str(fixmate_python_path.resolve()))

                fixmate_config_path = fixmate_path / _CONFIG_NAME
                if fixmate_config_path.is_file():
                    inputs = yaml.safe_load(fixmate_config_path.read_text()) or {}
                    logger.info(f"Input values loaded from {fixmate_config_path}")
                else:
                    logger.debug(
                        f'Config file "{fixmate_config_path}" not found from directory {config}, using default config'
                    )

                fixmate_prompt_path = fixmate_path / _PROMPT_NAME
                if fixmate_prompt_path.is_file():
                    inputs[PROMPT_TEMPLATE_FILE_KEY] = fixmate_prompt_path
                    logger.info(f"Prompt template loaded from {fixmate_prompt_path}")
                else:
                    logger.debug(
                        f'Prompt file "{fixmate_prompt_path}" not found from directory {config}, using default prompt'
                    )
            else:
                logger.error(f"Config path {config} is neither a file nor a directory")
                exit(1)
        print("possosos", possbile_module_paths, fixflow_name)
        fixflow_class = find_fixflow(possbile_module_paths, fixflow_name)
        if fixflow_class is None:
            logger.error(f"Patchflow {fixflow_name} not found in {possbile_module_paths}")
            exit(1)

    for opt in opts:
        key, equal_sign, value = opt.partition("=")
        key = key.lstrip("-")

        if equal_sign == "":
            # treat --key as a flag
            inputs[key] = True
        else:
            # treat --key=value as a key-value pair
            inputs[key] = value

    with logger.panel(f"Patchflow {fixflow} logs") as _:
        try:
            fixed = PatchedClient(inputs.get("fixed_api_key"))
            if not disable_telemetry:
                fixed.send_public_telemetry(fixflow_name, inputs)

            with fixed.fixed_telemetry(fixflow_name, {}):
                fixflow_instance = fixflow_class(inputs)
                fixflow_instance.run()
        except Exception as e:
            logger.debug(traceback.format_exc())
            logger.error(f"Error running fixflow {fixflow}: {e}")
            exit(1)

    if output is not None:
        serialize = _DATA_FORMAT_MAPPING.get(data_format, json.dumps)
        with open(output, "w") as file:
            file.write(serialize(inputs))


# if __name__ == "__main__":
#     # cli()
def run_func():
    inputs = {}
    module_path = _PATCHFLOW_MODULE_NAME
    possbile_module_paths = deque((module_path,))
    fixflow_name = 'AutoFix'
    print("kdsndskjkd", possbile_module_paths)
    # fixflow_class = find_fixflow(possbile_module_paths, fixflow_name)
    from .fixflows.AutoFix.AutoFix import AutoFix
    fixflow_class = AutoFix
    print("kdnfds", fixflow_class)
    fixflow_instance = fixflow_class(inputs)
    fixflow_instance.run()
