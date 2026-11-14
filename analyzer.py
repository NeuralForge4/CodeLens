import ast
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

MODEL_DIR = Path(__file__).parent / "artifacts"
MAX_CODE_CHARS = 100_000


def _syntax_check(code):
    try:
        ast.parse(code)
        return None
    except SyntaxError as exc:
        return {
            "tool": "Python parser", "severity": "error",
            "line": exc.lineno or 1, "column": exc.offset or 1,
            "message": exc.msg, "suggestion": "Fix the syntax error before interpreting other results."
        }


def _ast_checks(code):
    findings = []
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return findings

    imports = []
    used_names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                bound = alias.asname or alias.name.split(".")[0]
                imports.append((bound, node.lineno, alias.name))
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            findings.append({
                "tool": "AST rule", "severity": "warning", "line": node.lineno,
                "message": "Bare 'except:' catches every exception, including system-exiting exceptions.",
                "suggestion": "Catch a specific exception type, such as ValueError or OSError."
            })
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "eval":
            findings.append({
                "tool": "AST rule", "severity": "high", "line": node.lineno,
                "message": "Use of eval() can execute dynamically constructed code.",
                "suggestion": "Avoid eval(); parse the expected input format explicitly."
            })
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "exec":
            findings.append({
                "tool": "AST rule", "severity": "high", "line": node.lineno,
                "message": "Use of exec() executes dynamically supplied Python code.",
                "suggestion": "Replace dynamic execution with explicit functions or data-driven logic."
            })
        if isinstance(node, ast.FunctionDef) and len(node.body) > 50:
            findings.append({
                "tool": "AST rule", "severity": "info", "line": node.lineno,
                "message": f"Function '{node.name}' has a large body ({len(node.body)} top-level statements).",
                "suggestion": "Consider splitting this function into smaller, single-purpose functions."
            })

    for name, line, original in imports:
        if name not in used_names:
            findings.append({
                "tool": "AST rule", "severity": "warning", "line": line,
                "message": f"Imported name '{original}' does not appear to be used.",
                "suggestion": "Remove the import if it is unnecessary."
            })

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            args = [a.arg for a in node.args.args]
            if len(args) > 7:
                findings.append({
                    "tool": "AST rule", "severity": "info", "line": node.lineno,
                    "message": f"Function '{node.name}' has {len(args)} parameters.",
                    "suggestion": "Consider grouping related parameters into a dataclass or configuration object."
                })
    return findings


def _run_ruff(code):
    """Run Ruff on a temporary file; source is linted, never executed."""
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", encoding="utf-8", delete=False) as f:
            f.write(code)
            path = f.name
        proc = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "--output-format", "json", path],
            capture_output=True, text=True, timeout=8
        )
        if proc.returncode not in (0, 1) or not proc.stdout.strip():
            return [], "Ruff is not installed or could not run. Install dependencies to enable lint checks."
        raw = json.loads(proc.stdout)
        results = []
        for item in raw[:80]:
            code_id = item.get("code", "")
            results.append({
                "tool": "Ruff", "severity": "warning",
                "line": (item.get("location") or {}).get("row", 1),
                "message": f"{code_id}: {item.get('message', 'Lint issue')}",
                "suggestion": "Review the lint rule and apply the suggested fix if appropriate."
            })
        return results, None
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return [], "Ruff could not run in this environment."
    finally:
        try:
            os.unlink(path)
        except (UnboundLocalError, OSError):
            pass


def _complexity(code):
    try:
        from radon.complexity import cc_visit
        blocks = cc_visit(code)
        return [
            {"name": b.name, "type": b.__class__.__name__, "complexity": b.complexity,
             "rank": _complexity_rank(b.complexity), "line": b.lineno}
            for b in blocks[:100]
        ]
    except Exception:
        return []


def _complexity_rank(value):
    if value <= 5: return "A - low"
    if value <= 10: return "B - moderate"
    if value <= 20: return "C - elevated"
    if value <= 30: return "D - high"
    return "E - very high"



def _ml_prediction(code):
    """Use the trained TF-IDF + Logistic Regression classifier."""
    model_file = MODEL_DIR / "defect_classifier.joblib"

    if not model_file.exists():
        return None, "No trained ML classifier found. Run train_model.py first."

    try:
        import joblib

        model = joblib.load(model_file)

        probabilities = model.predict_proba([code])[0]
        classes = list(model.classes_)

        if 1 not in classes:
            return None, "The trained model does not contain the defective-code class."

        defect_index = classes.index(1)
        score = float(probabilities[defect_index]) * 100

        return round(score, 1), None

    except Exception as exc:
        return None, f"ML classifier could not be loaded: {exc}"


def analyze_code(code, filename="pasted_code.py"):
    if len(code) > MAX_CODE_CHARS:
        raise ValueError("Source code is too large.")
    syntax = _syntax_check(code)
    findings = []
    if syntax:
        findings.append(syntax)
    else:
        findings.extend(_ast_checks(code))
        ruff_findings, ruff_note = _run_ruff(code)
        findings.extend(ruff_findings)

    complexity = _complexity(code) if not syntax else []
    lines = code.splitlines()
    nonblank = sum(1 for line in lines if line.strip())
    high = sum(1 for f in findings if f["severity"] == "high" or f["severity"] == "error")
    warnings = sum(1 for f in findings if f["severity"] == "warning")
    # This is a transparent rule-based indicator, not a trained defect probability.
    heuristic_score = min(95, high * 22 + warnings * 9 + sum(1 for c in complexity if c["complexity"] > 10) * 8)
    ai_score, ai_note = _ml_prediction(code)
    return {
        "filename": filename,
        "summary": {
            "lines": len(lines), "nonblank_lines": nonblank,
            "findings": len(findings), "high": high, "warnings": warnings,
            "heuristic_risk": heuristic_score, "ml_defect_score": ai_score,
            "functions": sum(1 for n in ast.walk(ast.parse(code)) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))) if not syntax else 0
        },
        "findings": sorted(findings, key=lambda f: ({"error": 0, "high": 1, "warning": 2, "info": 3}.get(f["severity"], 4), f["line"])),
        "complexity": complexity,
        "notes": [n for n in [ai_note, (ruff_note if not syntax else None)] if n]
    }
