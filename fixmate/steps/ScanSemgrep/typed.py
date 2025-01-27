from typing_extensions import Annotated, Dict, TypedDict

from fixmate.common.utils.step_typing import StepTypeConfig


class ScanSemgrepInputs(TypedDict, total=False):
    sarif_file_path: Annotated[str, StepTypeConfig(is_config=True, is_path=True)]
    sarif_values: str
    semgrep_extra_args: Annotated[str, StepTypeConfig(is_config=True)]


class ScanSemgrepOutputs(TypedDict):
    sarif_values: dict
