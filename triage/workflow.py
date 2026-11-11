import json
import time
from concurrent.futures import ThreadPoolExecutor

from . import prompts
from .llm import LLMError, Usage
from .schemas import IOCs, Classification, FinalText, IncidentReport, RunResult, SeverityAssessment

# для доп. задания: ломаем один шаг и смотрим, что будет
FAULTS = {
    "fake_iocs": "шаг 2а добавляет выдуманные IOC",
    "ioc_step_fails": "шаг 2а всегда падает",
    "router_says_benign": "шаг 1 всегда отвечает benign",
}
FAKE_IOCS = IOCs(ips=["185.220.101.99"], domains=["evil-c2.example"], hashes=["deadbeefdeadbeefdeadbeefdeadbeef"])


def run_workflow(text, llm, fault=None):
    usage = Usage()
    start = time.time()
    problems = []

    def result(**kwargs):
        return RunResult(approach="workflow", seconds=time.time() - start, llm_calls=usage.calls,
                         tokens=usage.total_tokens, problems=problems, **kwargs)

    try:
        classification = llm.ask_json(prompts.CLASSIFY, prompts.wrap(text), Classification, usage)
    except LLMError as e:
        return result(success=False, error=f"шаг 1: {e}")
    if fault == "router_says_benign":
        classification = Classification(incident_type="benign", reasoning=classification.reasoning)
    steps = {"1_classification": classification.model_dump()}

    if classification.incident_type == "benign":
        report = IncidentReport(
            incident_type="benign",
            severity="low",
            summary=classification.reasoning,
            recommended_actions=["Закрыть алерт как ложное срабатывание.", "Проверить, нужно ли исключение в правиле SIEM."],
        )
        return result(success=True, report=report, steps=steps)

    with ThreadPoolExecutor(max_workers=2) as pool:
        f1 = pool.submit(extract_iocs, text, llm, usage, problems, fault)
        f2 = pool.submit(assess_severity, text, classification.incident_type, llm, usage, problems)
        iocs = f1.result()
        assessment = f2.result()

    iocs, removed = iocs.keep_only_found_in(text)
    steps["2a_iocs"] = iocs.model_dump()
    steps["2b_severity"] = assessment.model_dump()

    final = write_report(classification, iocs, assessment, llm, usage, problems)
    steps["3_text"] = final.model_dump()

    report = IncidentReport(
        incident_type=classification.incident_type,
        severity=assessment.severity,
        iocs=iocs,
        mitre_techniques=assessment.mitre_techniques,
        summary=final.summary,
        recommended_actions=final.recommended_actions,
        warnings=list(problems),
    )
    return result(success=True, report=report, removed_iocs=removed, steps=steps)


def extract_iocs(text, llm, usage, problems, fault=None):
    try:
        if fault == "ioc_step_fails":
            raise LLMError("искусственная ошибка")
        iocs = llm.ask_json(prompts.EXTRACT_IOCS, prompts.wrap(text), IOCs, usage)
    except LLMError as e:
        problems.append(f"IOC не извлечены, шаг 2а упал ({e})")
        return IOCs()
    if fault == "fake_iocs":
        iocs = IOCs(**{k: v + getattr(FAKE_IOCS, k) for k, v in iocs.model_dump().items()})
    return iocs


def assess_severity(text, incident_type, llm, usage, problems):
    try:
        return llm.ask_json(prompts.ASSESS_SEVERITY, prompts.severity_request(text, incident_type),
                            SeverityAssessment, usage)
    except LLMError as e:
        # лучше лишний раз проверить вручную, чем пропустить атаку, поэтому high
        problems.append(f"Критичность не оценена, шаг 2б упал, поставлено high ({e})")
        return SeverityAssessment(severity="high", reasoning="оценка недоступна")


def write_report(classification, iocs, assessment, llm, usage, problems):
    data = {
        "incident_type": classification.incident_type,
        "classification_reasoning": classification.reasoning,
        "iocs": iocs.model_dump(),
        "severity": assessment.severity,
        "mitre_techniques": assessment.mitre_techniques,
        "severity_reasoning": assessment.reasoning,
        "warnings": list(problems),
    }
    try:
        return llm.ask_json(prompts.WRITE_REPORT, json.dumps(data, ensure_ascii=False, indent=2), FinalText, usage)
    except LLMError as e:
        problems.append(f"Шаг 3 упал, текст собран по шаблону ({e})")
        return FinalText(
            summary=f"{classification.reasoning} Критичность: {assessment.severity}.",
            recommended_actions=["Проверить инцидент вручную."],
        )
