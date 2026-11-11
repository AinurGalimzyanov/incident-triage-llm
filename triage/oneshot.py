import time

from . import prompts
from .llm import LLMError, Usage
from .schemas import IncidentReport, RunResult


def run_oneshot(text, llm):
    usage = Usage()
    start = time.time()
    try:
        report = llm.ask_json(prompts.ONESHOT, prompts.wrap(text), IncidentReport, usage)
    except LLMError as e:
        return RunResult(approach="oneshot", success=False, error=str(e), seconds=time.time() - start,
                         llm_calls=usage.calls, tokens=usage.total_tokens)

    report.iocs, removed = report.iocs.keep_only_found_in(text)

    return RunResult(approach="oneshot", success=True, report=report, removed_iocs=removed,
                     seconds=time.time() - start, llm_calls=usage.calls, tokens=usage.total_tokens)
