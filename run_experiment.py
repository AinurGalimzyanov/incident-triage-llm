import argparse
import json
import sys
from pathlib import Path

from triage.evaluate import load_cases, markdown_table, score, summarize
from triage.llm import LLMClient, LLMError
from triage.oneshot import run_oneshot
from triage.schemas import RunResult
from triage.workflow import FAULTS, run_workflow

RESULTS = Path("results")


def run_all(name, solve, cases):
    print(f"\n=== {name} ===")
    runs = []
    for i, case in enumerate(cases, 1):
        run = solve(case["text"])
        run.case_id = case["id"]
        runs.append(run)
        if run.success:
            verdict = f"{run.report.incident_type}/{run.report.severity}"
        else:
            verdict = f"ОШИБКА: {run.error}"
        print(f"[{i:>2}/{len(cases)}] {case['id']:<28} {verdict:<28} {run.llm_calls} выз., {run.tokens} ток., {run.seconds:.1f} с")
        for problem in run.problems:
            print(f"        ! {problem}")
    RESULTS.mkdir(exist_ok=True)
    data = [r.model_dump() for r in runs]
    (RESULTS / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return runs


def per_case_table(cases, runs_by_name):
    names = list(runs_by_name)
    lines = ["| Кейс | Эталон | " + " | ".join(names) + " |", "|---|---|" + "---|" * len(names)]
    for i, case in enumerate(cases):
        exp = case["expected"]
        cells = []
        for name in names:
            row = score(runs_by_name[name][i], case)
            if not row["success"]:
                cells.append("ошибка")
            else:
                mark = "+" if row["type_ok"] else "-"
                cells.append(f"{mark} {row['type']} / {row['severity']}")
        star = " *" if case["ambiguous"] else ""
        lines.append(f"| {case['id']}{star} | {exp['incident_type']} / {exp['severity']} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n\n`*` - неоднозначный кейс, `+` - тип определен верно."


def main():
    # без этого в консоли PyCharm и Git Bash русский текст выводится нечитаемо
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, help="взять только первые N кейсов")
    parser.add_argument("--fault", choices=list(FAULTS), help="запустить workflow со сломанным шагом")
    args = parser.parse_args()

    cases = load_cases()[:args.limit]
    try:
        llm = LLMClient()
    except LLMError as e:
        sys.exit(str(e))
    print(f"Модель: {llm.model}, кейсов: {len(cases)}")

    if args.fault:
        saved = RESULTS / "workflow.json"
        if not saved.exists():
            sys.exit("Сначала запустите python run_experiment.py без --fault")
        saved_runs = {r["case_id"]: RunResult(**r) for r in json.loads(saved.read_text(encoding="utf-8"))}
        if any(case["id"] not in saved_runs for case in cases):
            sys.exit("В results/workflow.json не все кейсы, сначала запустите полное сравнение без --limit")
        runs = {
            "Workflow": [saved_runs[case["id"]] for case in cases],
            f"Workflow + {args.fault}": run_all(f"fault_{args.fault}", lambda t: run_workflow(t, llm, args.fault), cases),
        }
        title = f"# Сломанный шаг: {args.fault} ({FAULTS[args.fault]})"
        out_file = RESULTS / f"fault_{args.fault}.md"
    else:
        runs = {
            "One-shot": run_all("oneshot", lambda t: run_oneshot(t, llm), cases),
            "Workflow": run_all("workflow", lambda t: run_workflow(t, llm), cases),
        }
        title = "# Сравнение One-shot и Workflow"
        out_file = RESULTS / "summary.md"

    metrics = {name: summarize([score(r, c) for r, c in zip(rs, cases)]) for name, rs in runs.items()}
    removed = {name: sum(len(r.removed_iocs) for r in rs) for name, rs in runs.items()}
    report = "\n\n".join([
        title,
        f"Модель: `{llm.model}`, кейсов: {len(cases)}.",
        markdown_table(metrics),
        "Удалено выдуманных IOC: " + ", ".join(f"{name}: {n}" for name, n in removed.items()),
        "## По кейсам",
        per_case_table(cases, runs),
    ])
    out_file.write_text(report + "\n", encoding="utf-8")
    print("\n" + report)
    print(f"\nСохранено в {out_file}")


if __name__ == "__main__":
    main()
