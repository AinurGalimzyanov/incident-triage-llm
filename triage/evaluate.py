import json
from pathlib import Path

from .schemas import SEVERITY_ORDER


def load_cases(path="data/test_cases.json"):
    cases = json.loads(Path(path).read_text(encoding="utf-8"))
    for case in cases:
        case["text"] = "\n".join(case["input"])
    return cases


def compare_iocs(found, expected):
    # возвращает (найдено из эталона, всего в эталоне, лишних)
    # поддомен эталонного домена тоже считаем найденным
    expected_values = [v.lower() for values in expected.values() for v in values]
    found_values = [v.lower().rstrip("/") for values in found.model_dump().values() for v in values]
    matched = set()
    extra = 0
    for value in found_values:
        hits = [e for e in expected_values if value == e.rstrip("/") or value.endswith("." + e)]
        if hits:
            matched.update(hits)
        else:
            extra += 1
    return len(matched), len(expected_values), extra


def score(run, case):
    expected = case["expected"]
    # для benign IOC не считаем, там нечего искать
    is_attack = expected["incident_type"] != "benign"
    row = {
        "case": case["id"],
        "ambiguous": case["ambiguous"],
        "success": run.success,
        "type": None,
        "type_ok": False,
        "severity": None,
        "severity_ok": False,
        "severity_close": False,
        "ioc_found": 0,
        "ioc_expected": sum(len(v) for v in expected["iocs"].values()) if is_attack else 0,
        "ioc_extra": 0,
        "seconds": run.seconds,
        "llm_calls": run.llm_calls,
        "tokens": run.tokens,
    }
    if run.report is None:
        return row
    r = run.report
    row["type"] = r.incident_type
    row["type_ok"] = r.incident_type == expected["incident_type"] or r.incident_type in expected.get("also_ok", [])
    row["severity"] = r.severity
    row["severity_ok"] = r.severity == expected["severity"]
    diff = abs(SEVERITY_ORDER.index(r.severity) - SEVERITY_ORDER.index(expected["severity"]))
    row["severity_close"] = diff <= 1
    if is_attack:
        row["ioc_found"], _, row["ioc_extra"] = compare_iocs(r.iocs, expected["iocs"])
    return row


def summarize(rows):
    n = len(rows)
    found = sum(r["ioc_found"] for r in rows)
    expected = sum(r["ioc_expected"] for r in rows)
    extra = sum(r["ioc_extra"] for r in rows)
    ambiguous = [r for r in rows if r["ambiguous"]]
    return {
        "Доля успешных выполнений": sum(r["success"] for r in rows) / n,
        "Тип инцидента: accuracy": sum(r["type_ok"] for r in rows) / n,
        "Тип инцидента на неоднозначных": sum(r["type_ok"] for r in ambiguous) / len(ambiguous) if ambiguous else None,
        "Критичность: точно": sum(r["severity_ok"] for r in rows) / n,
        "Критичность: ±1 уровень": sum(r["severity_close"] for r in rows) / n,
        "IOC: полнота (recall)": found / expected if expected else None,
        "IOC: точность (precision)": found / (found + extra) if found + extra else None,
        "Среднее время, с": sum(r["seconds"] for r in rows) / n,
        "Среднее число LLM-вызовов": sum(r["llm_calls"] for r in rows) / n,
        "Средний расход токенов": sum(r["tokens"] for r in rows) / n,
    }


def markdown_table(metrics):
    names = list(metrics)
    lines = ["| Метрика | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
    for key in metrics[names[0]]:
        cells = []
        for name in names:
            value = metrics[name][key]
            if value is None:
                cells.append("-")
            elif key.startswith(("Доля", "Тип", "Критичность", "IOC")):
                cells.append(f"{value:.0%}")
            elif "токенов" in key:
                cells.append(f"{value:.0f}")
            else:
                cells.append(f"{value:.1f}")
        lines.append(f"| {key} | " + " | ".join(cells) + " |")
    return "\n".join(lines)
