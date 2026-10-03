"""Adapt the existing writer interface to a non-housing question list.

The default writer and its frozen replay requests remain unchanged. This adapter only binds
the output ids and the opening context to the supplied list; all evidence rules are reused.
"""

from copy import deepcopy

from readmark.writer import OTHER, WRITER_SCHEMA, ClaudeWriter, build_prompt, claude_cli


class QuestionListWriter(ClaudeWriter):
    def write(self, case_meta: dict, case_passages: list[dict], clauses: list[dict],
              policy_by_id: dict[str, dict]) -> dict:
        prompt = build_prompt(case_meta, case_passages, clauses, policy_by_id)
        # Replace only the housing introduction; retain the shared evidence/output rules.
        prompt = (
            "An officer reviews this application against the approved policy questions below. "
            "The officer decides; you do not decide it or recommend an outcome.\n\n"
            + prompt.split("\n\n", 1)[1]
        )
        schema = deepcopy(WRITER_SCHEMA)
        schema["properties"]["facts"]["items"]["properties"]["clause_id"]["enum"] = [
            *[c["clause_id"] for c in clauses], OTHER
        ]
        request = {"model": self.model, "prompt": prompt, "schema": schema}
        response = self.cache.call(
            "writer", request, lambda: claude_cli.generate(prompt, schema, self.model)
        )
        self.model_id = response["model"]
        return response["output"]
