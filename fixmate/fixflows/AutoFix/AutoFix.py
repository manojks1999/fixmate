import json
from enum import IntEnum
from pathlib import Path

import yaml

from fixmate.common.utils.progress_bar import PatchflowProgressBar
from fixmate.common.utils.step_typing import validate_steps_with_inputs
from fixmate.logger import logger
from fixmate.step import Step
from fixmate.steps import (
    LLM,
    # PR,
    CallLLM,
    # CommitChanges,
    # CreatePR,
    ExtractCode,
    ExtractModelResponse,
    ModifyCode,
    # PreparePR,
    PreparePrompt,
    ScanSemgrep,
)

_DEFAULT_PROMPT_JSON = Path(__file__).parent / "default_prompt.json"
_DEFAULT_INPUT_FILE = Path(__file__).parent / "defaults.yml"


class Compatibility(IntEnum):
    HIGH = 3
    MEDIUM = 2
    LOW = 1
    UNKNOWN = 0

    @staticmethod
    def from_str(value: str) -> "Compatibility":
        try:
            return Compatibility[value.upper()]
        except KeyError:
            logger.error(f"Invalid compatibility value: {value}")
            return Compatibility.UNKNOWN


class AutoFix(Step):
    def __init__(self, inputs: dict):
        # PatchflowProgressBar(self).register_steps(
        #     CallLLM,
        #     CommitChanges,
        #     CreatePR,
        #     ExtractCode,
        #     ExtractModelResponse,
        #     ModifyCode,
        #     PreparePR,
        #     PreparePrompt,
        #     ScanSemgrep,
        # )
        final_inputs = yaml.safe_load(_DEFAULT_INPUT_FILE.read_text())
        final_inputs.update(inputs)

        self.n = int(final_inputs.get("n", 1))
        self.compatibility_threshold = Compatibility.from_str(final_inputs["compatibility"])

        if "prompt_id" not in final_inputs.keys():
            final_inputs["prompt_id"] = "fixprompt"

        if "prompt_template_file" not in final_inputs.keys():
            final_inputs["prompt_template_file"] = _DEFAULT_PROMPT_JSON

        final_inputs["response_partitions"] = {
            "commit_message": ["A. Commit message:", "B. Change summary:"],
            "fix_message": ["B. Change summary:", "C. Compatibility Risk:"],
            "compatibility": ["C. Compatibility Risk:", "D. Fixed Code:"],
            "fix": ["D. Fixed Code:", "```", "\n", "```"],
        }
        final_inputs["pr_title"] = f"fixmate {self.__class__.__name__}"
        final_inputs["branch_prefix"] = f"{self.__class__.__name__.lower()}-"

        # validate_steps_with_inputs(
        #     set(final_inputs.keys()).union({"prompt_values"}), ScanSemgrep, ExtractCode, LLM, ModifyCode, PR
        # )
        self.inputs = final_inputs

    def run(self) -> dict:
        print("jsdkjnfkjdsnfksjndf")
        outputs = ScanSemgrep(self.inputs).run()
        print("raaaaaa", outputs)
        self.inputs.update(outputs)
        outputs = ExtractCode(self.inputs).run()
        self.inputs.update(outputs)
        print("inputttt", outputs)
        for i in range(self.n):
            self.inputs["prompt_values"] = outputs.get("files_to_fix", [])
            outputs = LLM(self.inputs).run()
            self.inputs.update(outputs)

            for extracted_response in self.inputs["extracted_responses"]:
                response_compatibility = Compatibility.from_str(
                    extracted_response.get("compatibility", "UNKNOWN").strip()
                )
                if response_compatibility < self.compatibility_threshold:
                    extracted_response.pop("fix", None)

            outputs = ModifyCode(self.inputs).run()
            self.inputs.update(outputs)

            if i == self.n - 1:
                break

            # validation
            self.inputs.pop("sarif_file_path", None)
            outputs = ScanSemgrep(self.inputs).run()
            self.inputs.update(outputs)
            outputs = ExtractCode(self.inputs).run()
            self.inputs.update(outputs)
            if self.inputs.get("prompt_value_file") is not None:
                with open(self.inputs["prompt_value_file"], "r") as fp:
                    vulns = json.load(fp)
                if len(vulns) < 1:
                    break


        return self.inputs
