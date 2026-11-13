"""Read-only documentation and AST inspection."""
import ast
import os
import re
from pathlib import Path
from .phrases import TAXFORMEXTRACTION, NOTAXFORMEXTRACTION, GENERIC_NAMES, AZURE_MODEL_IDS, VERYFI_NAMES


def normalize(text):
    return ' '.join(text.lower().replace('’', "'").replace("n't", ' not').replace('-', ' ').split())


def match_phrases(text, phrases):
    found = []
    for phrase in sorted(phrases, key=lambda p: (-len(p), p)):
        pattern = r'\b' + re.escape(phrase) + r'\b'
        if re.search(pattern, text):
            found.append(phrase)
            text = re.sub(pattern, ' ', text)
    return found, text


def claims(text):
    lines = []
    fence = None
    for line in text.splitlines():
        marker = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', line)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip():
                fence = None
        elif marker:
            fence = marker[1]
        else:
            lines.append(line)
    positive, negative = False, False
    for paragraph in re.split(r'\n\s*\n', '\n'.join(lines)):
        denials, rest = match_phrases(normalize(paragraph), NOTAXFORMEXTRACTION)
        affirmations, _ = match_phrases(rest, TAXFORMEXTRACTION)
        positive |= bool(affirmations)
        negative |= bool(denials)
    return positive, negative


def evidence(source):
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    nodes = list(ast.walk(tree))
    shadow = {n.name for n in nodes if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
    bound = set()
    for node in nodes:
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            targets = [i.optional_vars for i in node.items if i.optional_vars]
        for target in targets:
            bound.update(n.id for n in ast.walk(target) if isinstance(n, ast.Name))
    imports = {}
    azure_gate = veryfi_gate = False
    for node in nodes:
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports[alias.asname or alias.name.split('.')[0]] = alias.name if alias.asname else alias.name.split('.')[0]
                azure_gate |= alias.name in ('azure.ai.formrecognizer', 'azure.ai.documentintelligence')
                veryfi_gate |= alias.name == 'veryfi' or alias.name.startswith('veryfi.')
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            for alias in node.names:
                imports[alias.asname or alias.name] = module + '.' + alias.name
                full = module + '.' + alias.name
                azure_gate |= any(full == p or full.startswith(p + '.') for p in ('azure.ai.formrecognizer', 'azure.ai.documentintelligence'))
            veryfi_gate |= module == 'veryfi' or module.startswith('veryfi.')
    def resolve(node):
        if isinstance(node, ast.Name):
            return imports.get(node.id, '') if node.id not in bound | shadow else ''
        if isinstance(node, ast.Attribute):
            base = resolve(node.value)
            return base + '.' + node.attr if base else ''
        return ''
    def root_name(node):
        while isinstance(node, ast.Attribute):
            node = node.value
        return node.id if isinstance(node, ast.Name) else None
    azure_client = azure_call = veryfi_client = veryfi_call = generic = False
    for node in nodes:
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else func.id if isinstance(func, ast.Name) else ''
        if name in shadow:
            continue
        if isinstance(func, ast.Name) and func.id in bound:
            continue
        if isinstance(func, ast.Attribute) and root_name(func) in shadow:
            continue
        resolved = resolve(func)
        if isinstance(func, ast.Attribute) and name in GENERIC_NAMES:
            generic = True
        if isinstance(func, ast.Name) and resolved.split('.')[-1] in GENERIC_NAMES:
            generic = True
        if name in ('DocumentAnalysisClient', 'DocumentIntelligenceClient') or resolved in ('azure.ai.formrecognizer.DocumentAnalysisClient', 'azure.ai.documentintelligence.DocumentIntelligenceClient'):
            if resolved in ('azure.ai.formrecognizer.DocumentAnalysisClient', 'azure.ai.documentintelligence.DocumentIntelligenceClient') or (isinstance(func, ast.Attribute) and name in ('DocumentAnalysisClient', 'DocumentIntelligenceClient') and resolve(func.value).split('.')[0] == 'azure'):
                azure_client = True
        if isinstance(func, ast.Attribute) and name in ('begin_analyze_document', 'begin_analyze_document_from_url'):
            values = node.args[:1] + [k.value for k in node.keywords if k.arg == 'model_id']
            azure_call |= any(isinstance(v, ast.Constant) and isinstance(v.value, str) and v.value in AZURE_MODEL_IDS for v in values)
        if (isinstance(func, ast.Name) and resolved == 'veryfi.Client') or (isinstance(func, ast.Attribute) and name == 'Client' and isinstance(func.value, ast.Name) and func.value.id == 'veryfi' and resolve(func.value) == 'veryfi'):
            veryfi_client = True
        if isinstance(func, ast.Attribute) and name in VERYFI_NAMES:
            veryfi_call = True
    return generic or (azure_gate and azure_client and azure_call) or (veryfi_gate and veryfi_client and veryfi_call)


def audit(root, ignore=()):
    root = Path(root)
    if not root.is_dir():
        raise OSError('Repository must be a readable directory')
    if not os.access(root, os.R_OK | os.X_OK):
        raise OSError('Repository is unreadable')
    ignored = [Path(p).as_posix().strip('/') for p in ignore]
    positives, negatives, production, tests = [], [], [], []
    def excluded(rel):
        return any(rel == p or rel.startswith(p + '/') for p in ignored)
    for directory, dirs, files in os.walk(root, onerror=lambda error: (_ for _ in ()).throw(error), followlinks=False):
        dirs[:] = sorted(d for d in dirs if not (Path(directory)/d).is_symlink() and not excluded((Path(directory)/d).relative_to(root).as_posix()))
        for filename in sorted(files):
            path = Path(directory)/filename
            rel = path.relative_to(root)
            label = rel.as_posix()
            if path.is_symlink() or excluded(label):
                continue
            if label == 'README.md' or (path.suffix == '.md' and 'docs' in rel.parts):
                yes, no = claims(path.read_text(encoding='utf-8'))
                if yes: positives.append(label)
                if no: negatives.append(label)
            if path.suffix != '.py' or set(rel.parts[:-1]) & {'fixtures', 'docs', 'examples'}:
                continue
            if evidence(path.read_text(encoding='utf-8')):
                target = tests if 'tests' in rel.parts[:-1] or filename.startswith('test_') or filename.endswith('_test.py') else production
                target.append(label)
    findings = []
    if positives and not production:
        findings.append(dict(id='documented-tax-form-extraction-claim-false', severity='MEDIUM' if tests else 'HIGH', message='Documented capability lacks production evidence.' + (' Evidence exists only in tests.' if tests else ''), docs=sorted(positives)))
    if negatives and production:
        findings.append(dict(id='documented-no-tax-form-extraction-claim-false', severity='HIGH', message='Documented denial contradicts production evidence.', docs=sorted(negatives)))
    return dict(verdict='FAIL' if findings else 'PASS', findings=findings, production_evidence=sorted(production), test_evidence=sorted(tests))
