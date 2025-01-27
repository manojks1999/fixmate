from __future__ import annotations

from pathlib import Path

from fixmate.step import Step, StepStatus


def save_file_contents(file_path, content):
    """Utility function to save content to a file."""
    with open(file_path, "w") as file:
        file.write(content)


def handle_indent(src: list[str], target: list[str], start: int, end: int) -> list[str]:
    if len(target) < 1:
        return target

    if start == end:
        end = start + 1

    first_src_line = next((line for line in src[start:end] if line.strip() != ""), "")
    src_indent_count = len(first_src_line) - len(first_src_line.lstrip())
    first_target_line = next((line for line in target if line.strip() != ""), "")
    target_indent_count = len(first_target_line) - len(first_target_line.lstrip())
    indent_diff = src_indent_count - target_indent_count

    indent = ""
    if indent_diff > 0:
        indent_unit = first_src_line[0]
        indent = indent_unit * indent_diff

    return [indent + line for line in target]


def replace_code_in_file(
        file_path: str,
        start_line: int | None,
        end_line: int | None,
        new_code: str,
) -> None:
    path = Path(file_path)
    if path.exists() and start_line is not None and end_line is not None:
        """Replaces specified lines in a file with new code."""
        text = path.read_text()

        lines = text.splitlines(keepends=True)

        # Insert the new code at the start line after converting it into a list of lines
        lines[start_line:end_line] = handle_indent(lines, new_code.splitlines(keepends=True), start_line, end_line)
    else:
        lines = new_code.splitlines(keepends=True)

    # Save the modified contents back to the file
    save_file_contents(file_path, "".join(lines))


class ModifyCode(Step):
    UPDATED_SNIPPETS_KEY = "extracted_responses"
    FILES_TO_PATCH = "files_to_fix"
    required_keys = {FILES_TO_PATCH, UPDATED_SNIPPETS_KEY}

    def __init__(self, inputs: dict):
        super().__init__(inputs)
        if not all(key in inputs.keys() for key in self.required_keys):
            raise ValueError(f'Missing required data: "{self.required_keys}"')

        self.files_to_fix = inputs[self.FILES_TO_PATCH]
        self.extracted_responses = inputs[self.UPDATED_SNIPPETS_KEY]

    def run(self) -> dict:
        modified_code_files = []
        sorted_list = sorted(
            zip(self.files_to_fix, self.extracted_responses), key=lambda x: x[0]["startLine"], reverse=True
        )
        if len(sorted_list) == 0:
            self.set_status(StepStatus.SKIPPED, "No code snippets to modify.")
            return dict(modified_code_files=[])

        for code_snippet, extracted_response in sorted_list:
            uri = code_snippet.get("uri")
            start_line = code_snippet.get("startLine")
            end_line = code_snippet.get("endLine")
            new_code = extracted_response.get("fix")
            if new_code is None:
                continue

            replace_code_in_file(uri, start_line, end_line, new_code)
            modified_code_file = dict(path=uri, start_line=start_line, end_line=end_line, **extracted_response)
            modified_code_files.append(modified_code_file)

        return dict(modified_code_files=modified_code_files)
