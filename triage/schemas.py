import re
from typing import Literal

from pydantic import BaseModel, Field

IncidentType = Literal["brute_force", "web_attack", "malware", "phishing", "data_exfiltration", "benign", "unknown"]
Severity = Literal["low", "medium", "high", "critical"]
SEVERITY_ORDER = ["low", "medium", "high", "critical"]


class IOCs(BaseModel):
    ips: list[str] = []
    domains: list[str] = []
    urls: list[str] = []
    hashes: list[str] = []

    def keep_only_found_in(self, text):
        text = text.lower()
        kept, removed = {}, []
        for name in ["ips", "domains", "urls", "hashes"]:
            kept[name] = []
            for value in getattr(self, name):
                value = value.strip()
                if name == "ips":
                    # чтобы 192.0.2.1 не находился внутри 192.0.2.10
                    found = re.search(rf"(?<![\d.]){re.escape(value)}(?!\d)", text) is not None
                else:
                    found = value.lower() in text
                if value and found:
                    kept[name].append(value)
                else:
                    removed.append(value)
        return IOCs(**kept), removed


class IncidentReport(BaseModel):
    incident_type: IncidentType
    severity: Severity
    iocs: IOCs = IOCs()
    mitre_techniques: list[str] = []
    summary: str
    recommended_actions: list[str] = []
    warnings: list[str] = []


class Classification(BaseModel):
    incident_type: IncidentType
    reasoning: str


class SeverityAssessment(BaseModel):
    severity: Severity
    mitre_techniques: list[str] = []
    reasoning: str


class FinalText(BaseModel):
    summary: str
    recommended_actions: list[str]


class RunResult(BaseModel):
    approach: str
    case_id: str = ""
    success: bool
    report: IncidentReport | None = None
    error: str | None = None
    seconds: float = 0.0
    llm_calls: int = 0
    tokens: int = 0
    removed_iocs: list[str] = []
    problems: list[str] = []
    steps: dict = Field(default_factory=dict)
