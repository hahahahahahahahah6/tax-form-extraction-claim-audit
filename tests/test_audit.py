import ast
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from tax_form_extraction_claim_audit import phrases
from tax_form_extraction_claim_audit.audit import audit, evidence, claims
from tax_form_extraction_claim_audit.__main__ import main

class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
    def put(self, name, text):
        path = self.root/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path
    def cli(self, *args):
        with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()):
            code = main(['audit', str(self.root), *args])
        return code, out.getvalue()
    def test_phrase_oracle(self):
        tree = ast.parse(Path(phrases.__file__).read_text())
        values = {n.targets[0].id: ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)}
        self.assertEqual(values['TAXFORMEXTRACTION'], ('tax form extraction', 'extract tax forms', 'extracts tax forms', 'extracting tax forms', 'extract tax form', 'extracts tax form', 'extracting tax form', 'tax form parsing', 'tax form parser', 'parse tax forms', 'parses tax forms', 'parse tax form', 'parses tax form', 'tax document extraction', 'extract tax documents', 'extracts tax documents', 'extracting tax documents', 'extract tax document', 'extracts tax document', 'extracting tax document', 'tax return extraction', 'extract tax returns', 'extracts tax returns', 'extracting tax returns', 'extract tax return', 'extracts tax return', 'extracting tax return', 'w 2 extraction', 'extract w 2 forms', 'extracts w 2 forms', 'extracting w 2 forms', 'w 2 form extraction', 'extract w 2s', 'extracts w 2s', 'extracting w 2s', 'w2 extraction', 'extract w2 forms', 'w2 form extraction', 'extract w2s', '1099 extraction', 'extract 1099 forms', 'extracts 1099 forms', 'extracting 1099 forms', '1099 form extraction', 'extract 1099s', '1040 extraction', 'extract 1040 forms', 'tax form data extraction', 'extract tax form data', 'tax form field extraction'))
        self.assertEqual(values['NOTAXFORMEXTRACTION'], ('no tax form extraction', 'does not extract tax forms', 'does not extract tax form', 'does not support tax form extraction', 'without tax form extraction', 'no tax document extraction', 'does not extract tax documents', 'does not extract tax document', 'does not support tax document extraction', 'without tax document extraction', 'no tax return extraction', 'does not extract tax returns', 'does not extract tax return', 'tax form extraction not supported', 'tax document extraction not supported', 'tax return extraction not supported', 'no tax form parser', 'does not parse tax forms', 'does not parse tax form', 'no w 2 extraction', 'does not extract w 2 forms', 'no 1099 extraction', 'does not extract 1099 forms', 'no tax form field extraction'))
        self.assertEqual(values['GENERIC_NAMES'], ('extract_tax_form', 'extract_tax_forms', 'parse_tax_form', 'parse_tax_forms', 'extract_tax_document', 'extract_tax_documents', 'parse_tax_document', 'parse_tax_documents', 'extract_tax_return', 'extract_tax_returns', 'parse_tax_return', 'parse_tax_returns', 'extract_w2', 'extract_w2s', 'parse_w2', 'parse_w2s', 'extract_1099', 'extract_1099s', 'parse_1099', 'parse_1099s', 'tax_form_extraction', 'tax_form_extractor', 'tax_form_parser', 'extract_tax_form_data'))
        self.assertEqual(values['AZURE_MODEL_IDS'], ('prebuilt-tax.us', 'prebuilt-tax.us.w2', 'prebuilt-tax.us.W-4', 'prebuilt-tax.us.1095A', 'prebuilt-tax.us.1095C', 'prebuilt-tax.us.1098', 'prebuilt-tax.us.1098E', 'prebuilt-tax.us.1098T', 'prebuilt-tax.us.1099A', 'prebuilt-tax.us.1099B', 'prebuilt-tax.us.1099C', 'prebuilt-tax.us.1099CAP', 'prebuilt-tax.us.1099Combo', 'prebuilt-tax.us.1099DIV', 'prebuilt-tax.us.1099G', 'prebuilt-tax.us.1099H', 'prebuilt-tax.us.1099INT', 'prebuilt-tax.us.1099K', 'prebuilt-tax.us.1099LS', 'prebuilt-tax.us.1099LTC', 'prebuilt-tax.us.1099MISC', 'prebuilt-tax.us.1099NEC', 'prebuilt-tax.us.1099OID', 'prebuilt-tax.us.1099PATR', 'prebuilt-tax.us.1099Q', 'prebuilt-tax.us.1099QA', 'prebuilt-tax.us.1099R', 'prebuilt-tax.us.1099S', 'prebuilt-tax.us.1099SA', 'prebuilt-tax.us.1099SB', 'prebuilt-tax.us.1099SSA', 'prebuilt-tax.us.1040', 'prebuilt-tax.us.1040Schedule1', 'prebuilt-tax.us.1040Schedule2', 'prebuilt-tax.us.1040Schedule3', 'prebuilt-tax.us.1040Schedule8812', 'prebuilt-tax.us.1040ScheduleA', 'prebuilt-tax.us.1040ScheduleB', 'prebuilt-tax.us.1040ScheduleC', 'prebuilt-tax.us.1040ScheduleD', 'prebuilt-tax.us.1040ScheduleE', 'prebuilt-tax.us.1040ScheduleEIC', 'prebuilt-tax.us.1040ScheduleF', 'prebuilt-tax.us.1040ScheduleH', 'prebuilt-tax.us.1040ScheduleJ', 'prebuilt-tax.us.1040ScheduleR', 'prebuilt-tax.us.1040ScheduleSE', 'prebuilt-tax.us.1040Senior'))
    def test_bad(self):
        self.put('README.md', 'We extract tax forms.')
        result = audit(self.root)
        self.assertEqual(result['findings'][0]['id'], 'documented-tax-form-extraction-claim-false')
        self.assertEqual(result['findings'][0]['severity'], 'HIGH')
        self.assertEqual(self.cli()[0], 2)
    def test_good(self):
        self.put('README.md', 'We extract tax forms.')
        self.put('app.py', 'x.extract_tax_form(doc)')
        self.assertEqual(self.cli()[0], 0)
        self.assertEqual(audit(self.root)['verdict'], 'PASS')
    def test_denial(self):
        self.put('README.md', 'Does not extract tax forms.')
        self.assertEqual(audit(self.root)['verdict'], 'PASS')
        self.put('app.py', 'x.extract_tax_form(doc)')
        f = audit(self.root)['findings'][0]
        self.assertEqual(f['id'], 'documented-no-tax-form-extraction-claim-false')
        self.assertEqual(f['severity'], 'HIGH')
        self.assertEqual(self.cli()[0], 2)
    def test_test_only(self):
        self.put('README.md', 'extract tax forms')
        self.put('tests/test_app.py', 'x.extract_tax_form(doc)')
        self.assertEqual(audit(self.root)['findings'][0]['severity'], 'MEDIUM')
        self.assertEqual(self.cli()[0], 0)
        self.assertEqual(self.cli('--fail-on', 'medium')[0], 2)
    def test_no_claim(self):
        self.put('README.md', 'A utility.')
        self.put('app.py', 'x.extract_tax_form(doc)')
        self.assertEqual(audit(self.root)['verdict'], 'PASS')
    def test_json(self):
        self.put('README.md', 'extract tax forms')
        code, text = self.cli('--json')
        self.assertEqual(code, 2)
        result = json.loads(text)
        self.assertEqual(result['verdict'], 'FAIL')
        self.assertIn('message', result['findings'][0])
    def test_split_modules(self):
        self.put('README.md', 'extract tax forms')
        self.put('one.py', 'import veryfi\nc = veryfi.Client()')
        self.put('two.py', 'c.process_w2_document(doc)')
        self.assertEqual(self.cli()[0], 2)
    def test_symlinks(self):
        self.put('README.md', 'extract tax forms')
        target = self.put('fixtures/source.py', 'x.extract_tax_form(doc)')
        (self.root/'app.py').symlink_to(target)
        (self.root/'linked').symlink_to(target.parent, target_is_directory=True)
        self.assertEqual(self.cli()[0], 2)
    def test_docs_and_ignore(self):
        self.put('nested/docs/a.md', 'extract tax forms')
        self.assertEqual(self.cli()[0], 2)
        self.assertEqual(self.cli('--ignore', 'nested/docs')[0], 0)
        self.assertEqual(self.cli('--ignore', 'nested/doc')[0], 2)
    def test_usage(self):
        for args in ([], ['oops'], ['audit', '--fail-on', 'HIGH'], ['audit', '--ignore', 'a', 'b', 'c']):
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                main(args)
            self.assertEqual(caught.exception.code, 1)
    def test_bad_path(self):
        with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(['audit', str(self.root/'missing')]), 1)
    def test_entry_points(self):
        result = subprocess.run([sys.executable, '-m', 'tax_form_extraction_claim_audit', '--version'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), '0.1.0')
    def test_console_entry(self):
        import shutil
        executable = shutil.which('tax-form-extraction-claim-audit')
        if executable:
            result = subprocess.run([executable, '--version'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), '0.1.0')
        else:
            project = Path(__file__).resolve().parents[1]/'pyproject.toml'
            self.assertIn('tax-form-extraction-claim-audit = "tax_form_extraction_claim_audit.__main__:main"', project.read_text())
            with contextlib.redirect_stdout(io.StringIO()) as output, self.assertRaises(SystemExit) as caught:
                main(['--version'])
            self.assertEqual(caught.exception.code, 0)
            self.assertEqual(output.getvalue().strip(), '0.1.0')
    def test_veryfi_attribute_requires_exact_base(self):
        self.assertFalse(evidence('import veryfi as v\nc=v.Client()\nc.process_w2_document(doc)'))
    def test_positive_phrase_00(self):
        self.assertEqual(claims('tax form extraction'), (True, False))
    def test_positive_phrase_01(self):
        self.assertEqual(claims('extract tax forms'), (True, False))
    def test_positive_phrase_02(self):
        self.assertEqual(claims('extracts tax forms'), (True, False))
    def test_positive_phrase_03(self):
        self.assertEqual(claims('extracting tax forms'), (True, False))
    def test_positive_phrase_04(self):
        self.assertEqual(claims('extract tax form'), (True, False))
    def test_positive_phrase_05(self):
        self.assertEqual(claims('extracts tax form'), (True, False))
    def test_positive_phrase_06(self):
        self.assertEqual(claims('extracting tax form'), (True, False))
    def test_positive_phrase_07(self):
        self.assertEqual(claims('tax form parsing'), (True, False))
    def test_positive_phrase_08(self):
        self.assertEqual(claims('tax form parser'), (True, False))
    def test_positive_phrase_09(self):
        self.assertEqual(claims('parse tax forms'), (True, False))
    def test_positive_phrase_10(self):
        self.assertEqual(claims('parses tax forms'), (True, False))
    def test_positive_phrase_11(self):
        self.assertEqual(claims('parse tax form'), (True, False))
    def test_positive_phrase_12(self):
        self.assertEqual(claims('parses tax form'), (True, False))
    def test_positive_phrase_13(self):
        self.assertEqual(claims('tax document extraction'), (True, False))
    def test_positive_phrase_14(self):
        self.assertEqual(claims('extract tax documents'), (True, False))
    def test_positive_phrase_15(self):
        self.assertEqual(claims('extracts tax documents'), (True, False))
    def test_positive_phrase_16(self):
        self.assertEqual(claims('extracting tax documents'), (True, False))
    def test_positive_phrase_17(self):
        self.assertEqual(claims('extract tax document'), (True, False))
    def test_positive_phrase_18(self):
        self.assertEqual(claims('extracts tax document'), (True, False))
    def test_positive_phrase_19(self):
        self.assertEqual(claims('extracting tax document'), (True, False))
    def test_positive_phrase_20(self):
        self.assertEqual(claims('tax return extraction'), (True, False))
    def test_positive_phrase_21(self):
        self.assertEqual(claims('extract tax returns'), (True, False))
    def test_positive_phrase_22(self):
        self.assertEqual(claims('extracts tax returns'), (True, False))
    def test_positive_phrase_23(self):
        self.assertEqual(claims('extracting tax returns'), (True, False))
    def test_positive_phrase_24(self):
        self.assertEqual(claims('extract tax return'), (True, False))
    def test_positive_phrase_25(self):
        self.assertEqual(claims('extracts tax return'), (True, False))
    def test_positive_phrase_26(self):
        self.assertEqual(claims('extracting tax return'), (True, False))
    def test_positive_phrase_27(self):
        self.assertEqual(claims('w 2 extraction'), (True, False))
    def test_positive_phrase_28(self):
        self.assertEqual(claims('extract w 2 forms'), (True, False))
    def test_positive_phrase_29(self):
        self.assertEqual(claims('extracts w 2 forms'), (True, False))
    def test_positive_phrase_30(self):
        self.assertEqual(claims('extracting w 2 forms'), (True, False))
    def test_positive_phrase_31(self):
        self.assertEqual(claims('w 2 form extraction'), (True, False))
    def test_positive_phrase_32(self):
        self.assertEqual(claims('extract w 2s'), (True, False))
    def test_positive_phrase_33(self):
        self.assertEqual(claims('extracts w 2s'), (True, False))
    def test_positive_phrase_34(self):
        self.assertEqual(claims('extracting w 2s'), (True, False))
    def test_positive_phrase_35(self):
        self.assertEqual(claims('w2 extraction'), (True, False))
    def test_positive_phrase_36(self):
        self.assertEqual(claims('extract w2 forms'), (True, False))
    def test_positive_phrase_37(self):
        self.assertEqual(claims('w2 form extraction'), (True, False))
    def test_positive_phrase_38(self):
        self.assertEqual(claims('extract w2s'), (True, False))
    def test_positive_phrase_39(self):
        self.assertEqual(claims('1099 extraction'), (True, False))
    def test_positive_phrase_40(self):
        self.assertEqual(claims('extract 1099 forms'), (True, False))
    def test_positive_phrase_41(self):
        self.assertEqual(claims('extracts 1099 forms'), (True, False))
    def test_positive_phrase_42(self):
        self.assertEqual(claims('extracting 1099 forms'), (True, False))
    def test_positive_phrase_43(self):
        self.assertEqual(claims('1099 form extraction'), (True, False))
    def test_positive_phrase_44(self):
        self.assertEqual(claims('extract 1099s'), (True, False))
    def test_positive_phrase_45(self):
        self.assertEqual(claims('1040 extraction'), (True, False))
    def test_positive_phrase_46(self):
        self.assertEqual(claims('extract 1040 forms'), (True, False))
    def test_positive_phrase_47(self):
        self.assertEqual(claims('tax form data extraction'), (True, False))
    def test_positive_phrase_48(self):
        self.assertEqual(claims('extract tax form data'), (True, False))
    def test_positive_phrase_49(self):
        self.assertEqual(claims('tax form field extraction'), (True, False))
    def test_negative_phrase_00(self):
        self.assertEqual(claims('no tax form extraction'), (False, True))
    def test_negative_phrase_01(self):
        self.assertEqual(claims('does not extract tax forms'), (False, True))
    def test_negative_phrase_02(self):
        self.assertEqual(claims('does not extract tax form'), (False, True))
    def test_negative_phrase_03(self):
        self.assertEqual(claims('does not support tax form extraction'), (False, True))
    def test_negative_phrase_04(self):
        self.assertEqual(claims('without tax form extraction'), (False, True))
    def test_negative_phrase_05(self):
        self.assertEqual(claims('no tax document extraction'), (False, True))
    def test_negative_phrase_06(self):
        self.assertEqual(claims('does not extract tax documents'), (False, True))
    def test_negative_phrase_07(self):
        self.assertEqual(claims('does not extract tax document'), (False, True))
    def test_negative_phrase_08(self):
        self.assertEqual(claims('does not support tax document extraction'), (False, True))
    def test_negative_phrase_09(self):
        self.assertEqual(claims('without tax document extraction'), (False, True))
    def test_negative_phrase_10(self):
        self.assertEqual(claims('no tax return extraction'), (False, True))
    def test_negative_phrase_11(self):
        self.assertEqual(claims('does not extract tax returns'), (False, True))
    def test_negative_phrase_12(self):
        self.assertEqual(claims('does not extract tax return'), (False, True))
    def test_negative_phrase_13(self):
        self.assertEqual(claims('tax form extraction not supported'), (False, True))
    def test_negative_phrase_14(self):
        self.assertEqual(claims('tax document extraction not supported'), (False, True))
    def test_negative_phrase_15(self):
        self.assertEqual(claims('tax return extraction not supported'), (False, True))
    def test_negative_phrase_16(self):
        self.assertEqual(claims('no tax form parser'), (False, True))
    def test_negative_phrase_17(self):
        self.assertEqual(claims('does not parse tax forms'), (False, True))
    def test_negative_phrase_18(self):
        self.assertEqual(claims('does not parse tax form'), (False, True))
    def test_negative_phrase_19(self):
        self.assertEqual(claims('no w 2 extraction'), (False, True))
    def test_negative_phrase_20(self):
        self.assertEqual(claims('does not extract w 2 forms'), (False, True))
    def test_negative_phrase_21(self):
        self.assertEqual(claims('no 1099 extraction'), (False, True))
    def test_negative_phrase_22(self):
        self.assertEqual(claims('does not extract 1099 forms'), (False, True))
    def test_negative_phrase_23(self):
        self.assertEqual(claims('no tax form field extraction'), (False, True))
    def test_route_000(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us', doc)"), True)
    def test_route_001(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.w2', doc)"), True)
    def test_route_002(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.W-4', doc)"), True)
    def test_route_003(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1095A', doc)"), True)
    def test_route_004(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1095C', doc)"), True)
    def test_route_005(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1098', doc)"), True)
    def test_route_006(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1098E', doc)"), True)
    def test_route_007(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1098T', doc)"), True)
    def test_route_008(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1099A', doc)"), True)
    def test_route_009(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1099B', doc)"), True)
    def test_route_010(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1099C', doc)"), True)
    def test_route_011(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1099CAP', doc)"), True)
    def test_route_012(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1099Combo', doc)"), True)
    def test_route_013(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1099DIV', doc)"), True)
    def test_route_014(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1099G', doc)"), True)
    def test_route_015(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1099H', doc)"), True)
    def test_route_016(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1099INT', doc)"), True)
    def test_route_017(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1099K', doc)"), True)
    def test_route_018(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1099LS', doc)"), True)
    def test_route_019(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1099LTC', doc)"), True)
    def test_route_020(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1099MISC', doc)"), True)
    def test_route_021(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1099NEC', doc)"), True)
    def test_route_022(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1099OID', doc)"), True)
    def test_route_023(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1099PATR', doc)"), True)
    def test_route_024(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1099Q', doc)"), True)
    def test_route_025(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1099QA', doc)"), True)
    def test_route_026(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1099R', doc)"), True)
    def test_route_027(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1099S', doc)"), True)
    def test_route_028(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1099SA', doc)"), True)
    def test_route_029(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1099SB', doc)"), True)
    def test_route_030(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1099SSA', doc)"), True)
    def test_route_031(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1040', doc)"), True)
    def test_route_032(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1040Schedule1', doc)"), True)
    def test_route_033(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1040Schedule2', doc)"), True)
    def test_route_034(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1040Schedule3', doc)"), True)
    def test_route_035(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1040Schedule8812', doc)"), True)
    def test_route_036(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1040ScheduleA', doc)"), True)
    def test_route_037(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1040ScheduleB', doc)"), True)
    def test_route_038(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1040ScheduleC', doc)"), True)
    def test_route_039(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1040ScheduleD', doc)"), True)
    def test_route_040(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1040ScheduleE', doc)"), True)
    def test_route_041(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1040ScheduleEIC', doc)"), True)
    def test_route_042(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1040ScheduleF', doc)"), True)
    def test_route_043(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1040ScheduleH', doc)"), True)
    def test_route_044(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1040ScheduleJ', doc)"), True)
    def test_route_045(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1040ScheduleR', doc)"), True)
    def test_route_046(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1040ScheduleSE', doc)"), True)
    def test_route_047(self):
        self.assertEqual(evidence("from azure.ai.formrecognizer import DocumentAnalysisClient as C\nc=C()\nc.begin_analyze_document('prebuilt-tax.us.1040Senior', doc)"), True)
    def test_route_048(self):
        self.assertEqual(evidence('from azure.ai.documentintelligence import DocumentIntelligenceClient as C\nc=C()\nc.begin_analyze_document_from_url("prebuilt-tax.us.w2", url)'), True)
    def test_route_049(self):
        self.assertEqual(evidence('import azure.ai.documentintelligence as di\nc=di.DocumentIntelligenceClient()\nc.begin_analyze_document(model_id="prebuilt-tax.us.1099NEC")'), True)
    def test_route_050(self):
        self.assertEqual(evidence('from azure.ai import formrecognizer as fr\nc=fr.DocumentAnalysisClient()\nc.begin_analyze_document("prebuilt-tax.us")'), True)
    def test_route_051(self):
        self.assertEqual(evidence('x.extract_tax_form(doc)'), True)
    def test_route_052(self):
        self.assertEqual(evidence('from engine import extract_tax_form as operation\noperation(doc)'), True)
    def test_route_053(self):
        self.assertEqual(evidence('x.extract_tax_forms(doc)'), True)
    def test_route_054(self):
        self.assertEqual(evidence('from engine import extract_tax_forms as operation\noperation(doc)'), True)
    def test_route_055(self):
        self.assertEqual(evidence('x.parse_tax_form(doc)'), True)
    def test_route_056(self):
        self.assertEqual(evidence('from engine import parse_tax_form as operation\noperation(doc)'), True)
    def test_route_057(self):
        self.assertEqual(evidence('x.parse_tax_forms(doc)'), True)
    def test_route_058(self):
        self.assertEqual(evidence('from engine import parse_tax_forms as operation\noperation(doc)'), True)
    def test_route_059(self):
        self.assertEqual(evidence('x.extract_tax_document(doc)'), True)
    def test_route_060(self):
        self.assertEqual(evidence('from engine import extract_tax_document as operation\noperation(doc)'), True)
    def test_route_061(self):
        self.assertEqual(evidence('x.extract_tax_documents(doc)'), True)
    def test_route_062(self):
        self.assertEqual(evidence('from engine import extract_tax_documents as operation\noperation(doc)'), True)
    def test_route_063(self):
        self.assertEqual(evidence('x.parse_tax_document(doc)'), True)
    def test_route_064(self):
        self.assertEqual(evidence('from engine import parse_tax_document as operation\noperation(doc)'), True)
    def test_route_065(self):
        self.assertEqual(evidence('x.parse_tax_documents(doc)'), True)
    def test_route_066(self):
        self.assertEqual(evidence('from engine import parse_tax_documents as operation\noperation(doc)'), True)
    def test_route_067(self):
        self.assertEqual(evidence('x.extract_tax_return(doc)'), True)
    def test_route_068(self):
        self.assertEqual(evidence('from engine import extract_tax_return as operation\noperation(doc)'), True)
    def test_route_069(self):
        self.assertEqual(evidence('x.extract_tax_returns(doc)'), True)
    def test_route_070(self):
        self.assertEqual(evidence('from engine import extract_tax_returns as operation\noperation(doc)'), True)
    def test_route_071(self):
        self.assertEqual(evidence('x.parse_tax_return(doc)'), True)
    def test_route_072(self):
        self.assertEqual(evidence('from engine import parse_tax_return as operation\noperation(doc)'), True)
    def test_route_073(self):
        self.assertEqual(evidence('x.parse_tax_returns(doc)'), True)
    def test_route_074(self):
        self.assertEqual(evidence('from engine import parse_tax_returns as operation\noperation(doc)'), True)
    def test_route_075(self):
        self.assertEqual(evidence('x.extract_w2(doc)'), True)
    def test_route_076(self):
        self.assertEqual(evidence('from engine import extract_w2 as operation\noperation(doc)'), True)
    def test_route_077(self):
        self.assertEqual(evidence('x.extract_w2s(doc)'), True)
    def test_route_078(self):
        self.assertEqual(evidence('from engine import extract_w2s as operation\noperation(doc)'), True)
    def test_route_079(self):
        self.assertEqual(evidence('x.parse_w2(doc)'), True)
    def test_route_080(self):
        self.assertEqual(evidence('from engine import parse_w2 as operation\noperation(doc)'), True)
    def test_route_081(self):
        self.assertEqual(evidence('x.parse_w2s(doc)'), True)
    def test_route_082(self):
        self.assertEqual(evidence('from engine import parse_w2s as operation\noperation(doc)'), True)
    def test_route_083(self):
        self.assertEqual(evidence('x.extract_1099(doc)'), True)
    def test_route_084(self):
        self.assertEqual(evidence('from engine import extract_1099 as operation\noperation(doc)'), True)
    def test_route_085(self):
        self.assertEqual(evidence('x.extract_1099s(doc)'), True)
    def test_route_086(self):
        self.assertEqual(evidence('from engine import extract_1099s as operation\noperation(doc)'), True)
    def test_route_087(self):
        self.assertEqual(evidence('x.parse_1099(doc)'), True)
    def test_route_088(self):
        self.assertEqual(evidence('from engine import parse_1099 as operation\noperation(doc)'), True)
    def test_route_089(self):
        self.assertEqual(evidence('x.parse_1099s(doc)'), True)
    def test_route_090(self):
        self.assertEqual(evidence('from engine import parse_1099s as operation\noperation(doc)'), True)
    def test_route_091(self):
        self.assertEqual(evidence('x.tax_form_extraction(doc)'), True)
    def test_route_092(self):
        self.assertEqual(evidence('from engine import tax_form_extraction as operation\noperation(doc)'), True)
    def test_route_093(self):
        self.assertEqual(evidence('x.tax_form_extractor(doc)'), True)
    def test_route_094(self):
        self.assertEqual(evidence('from engine import tax_form_extractor as operation\noperation(doc)'), True)
    def test_route_095(self):
        self.assertEqual(evidence('x.tax_form_parser(doc)'), True)
    def test_route_096(self):
        self.assertEqual(evidence('from engine import tax_form_parser as operation\noperation(doc)'), True)
    def test_route_097(self):
        self.assertEqual(evidence('x.extract_tax_form_data(doc)'), True)
    def test_route_098(self):
        self.assertEqual(evidence('from engine import extract_tax_form_data as operation\noperation(doc)'), True)
    def test_route_099(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.process_w2_document(doc)'), True)
    def test_route_100(self):
        self.assertEqual(evidence('from veryfi import Client as C\nc=C()\nc.process_w2_document(doc)'), True)
    def test_route_101(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.process_w2_document_url(doc)'), True)
    def test_route_102(self):
        self.assertEqual(evidence('from veryfi import Client as C\nc=C()\nc.process_w2_document_url(doc)'), True)
    def test_route_103(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.process_w9_document(doc)'), True)
    def test_route_104(self):
        self.assertEqual(evidence('from veryfi import Client as C\nc=C()\nc.process_w9_document(doc)'), True)
    def test_route_105(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.process_w9_document_url(doc)'), True)
    def test_route_106(self):
        self.assertEqual(evidence('from veryfi import Client as C\nc=C()\nc.process_w9_document_url(doc)'), True)
    def test_route_107(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.process_w8_document(doc)'), True)
    def test_route_108(self):
        self.assertEqual(evidence('from veryfi import Client as C\nc=C()\nc.process_w8_document(doc)'), True)
    def test_route_109(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.process_w8_document_url(doc)'), True)
    def test_route_110(self):
        self.assertEqual(evidence('from veryfi import Client as C\nc=C()\nc.process_w8_document_url(doc)'), True)
    def test_excluded_000(self):
        self.assertEqual(evidence('import veryfi'), False)
    def test_excluded_001(self):
        self.assertEqual(evidence('import azure.ai.formrecognizer'), False)
    def test_excluded_002(self):
        self.assertEqual(evidence('import mindee'), False)
    def test_excluded_003(self):
        self.assertEqual(evidence('import azure.ai.documentintelligence\nc=azure.ai.documentintelligence.DocumentIntelligenceClient()'), False)
    def test_excluded_004(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()'), False)
    def test_excluded_005(self):
        self.assertEqual(evidence('def extract_tax_form(doc): pass\nextract_tax_form(doc)'), False)
    def test_excluded_006(self):
        self.assertEqual(evidence('def extract_tax_form(doc): pass\nx.extract_tax_form(doc)'), False)
    def test_excluded_007(self):
        self.assertEqual(evidence('class extract_tax_form: pass\nx.extract_tax_form(doc)'), False)
    def test_excluded_008(self):
        self.assertEqual(evidence('class X:\n def extract_tax_form(self): pass\nx.extract_tax_form(doc)'), False)
    def test_excluded_009(self):
        self.assertEqual(evidence('extract_tax_form(doc)'), False)
    def test_excluded_010(self):
        self.assertEqual(evidence('x.extract_tax_form'), False)
    def test_excluded_011(self):
        self.assertEqual(evidence('# x.extract_tax_form(doc)\ns="x.extract_tax_form(doc)"'), False)
    def test_excluded_012(self):
        self.assertEqual(evidence('def broken('), False)
    def test_excluded_013(self):
        self.assertEqual(evidence('extract_tax_form = callback\nextract_tax_form(doc)'), False)
    def test_excluded_014(self):
        self.assertEqual(evidence('from engine import extract_tax_form\nextract_tax_form: object = callback\nextract_tax_form(doc)'), False)
    def test_excluded_015(self):
        self.assertEqual(evidence('from engine import extract_tax_form\nwith context() as extract_tax_form:\n extract_tax_form(doc)'), False)
    def test_excluded_016(self):
        self.assertEqual(evidence('from engine import extract_tax_form\nasync def f():\n async with context() as extract_tax_form:\n  extract_tax_form(doc)'), False)
    def test_excluded_017(self):
        self.assertEqual(evidence("import azure.ai.formrecognizer\nc=azure.ai.formrecognizer.DocumentAnalysisClient()\nc.begin_analyze_document('prebuilt-invoice')"), False)
    def test_excluded_018(self):
        self.assertEqual(evidence("import azure.ai.formrecognizer\nc=azure.ai.formrecognizer.DocumentAnalysisClient()\nc.begin_analyze_document('prebuilt-receipt')"), False)
    def test_excluded_019(self):
        self.assertEqual(evidence("import azure.ai.formrecognizer\nc=azure.ai.formrecognizer.DocumentAnalysisClient()\nc.begin_analyze_document('prebuilt-layout')"), False)
    def test_excluded_020(self):
        self.assertEqual(evidence("import azure.ai.formrecognizer\nc=azure.ai.formrecognizer.DocumentAnalysisClient()\nc.begin_analyze_document('prebuilt-read')"), False)
    def test_excluded_021(self):
        self.assertEqual(evidence("import azure.ai.formrecognizer\nc=azure.ai.formrecognizer.DocumentAnalysisClient()\nc.begin_analyze_document('prebuilt-idDocument')"), False)
    def test_excluded_022(self):
        self.assertEqual(evidence("import azure.ai.formrecognizer\nc=azure.ai.formrecognizer.DocumentAnalysisClient()\nc.begin_analyze_document('prebuilt-check.us')"), False)
    def test_excluded_023(self):
        self.assertEqual(evidence("import azure.ai.formrecognizer\nc=azure.ai.formrecognizer.DocumentAnalysisClient()\nc.begin_analyze_document('prebuilt-payStub.us')"), False)
    def test_excluded_024(self):
        self.assertEqual(evidence("import azure.ai.formrecognizer\nc=azure.ai.formrecognizer.DocumentAnalysisClient()\nc.begin_analyze_document('prebuilt-bankStatement.us')"), False)
    def test_excluded_025(self):
        self.assertEqual(evidence("import azure.ai.formrecognizer\nc=azure.ai.formrecognizer.DocumentAnalysisClient()\nc.begin_analyze_document('prebuilt-tax')"), False)
    def test_excluded_026(self):
        self.assertEqual(evidence("import azure.ai.formrecognizer\nc=azure.ai.formrecognizer.DocumentAnalysisClient()\nc.begin_analyze_document('prebuilt-tax.us.w')"), False)
    def test_excluded_027(self):
        self.assertEqual(evidence("import azure.ai.formrecognizer\nc=azure.ai.formrecognizer.DocumentAnalysisClient()\nc.begin_analyze_document('prebuilt-tax.us.w-4')"), False)
    def test_excluded_028(self):
        self.assertEqual(evidence("import azure.ai.formrecognizer\nc=azure.ai.formrecognizer.DocumentAnalysisClient()\nc.begin_analyze_document('prebuilt-tax.us.1099')"), False)
    def test_excluded_029(self):
        self.assertEqual(evidence("import azure.ai.formrecognizer\nc=azure.ai.formrecognizer.DocumentAnalysisClient()\nc.begin_analyze_document('prebuilt-tax.us.W2')"), False)
    def test_excluded_030(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.process_document(doc)'), False)
    def test_excluded_031(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.process_document_url(doc)'), False)
    def test_excluded_032(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.process_check(doc)'), False)
    def test_excluded_033(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.process_check_url(doc)'), False)
    def test_excluded_034(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.process_check_with_remittance(doc)'), False)
    def test_excluded_035(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.process_check_with_remittance_url(doc)'), False)
    def test_excluded_036(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.process_bank_statement_document(doc)'), False)
    def test_excluded_037(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.process_bank_statement_document_url(doc)'), False)
    def test_excluded_038(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.classify_document(doc)'), False)
    def test_excluded_039(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.get_w2(doc)'), False)
    def test_excluded_040(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.get_w2s(doc)'), False)
    def test_excluded_041(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.delete_w2(doc)'), False)
    def test_excluded_042(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.get_w9(doc)'), False)
    def test_excluded_043(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.get_w9s(doc)'), False)
    def test_excluded_044(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.delete_w9(doc)'), False)
    def test_excluded_045(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.get_w8(doc)'), False)
    def test_excluded_046(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.get_w8s(doc)'), False)
    def test_excluded_047(self):
        self.assertEqual(evidence('import veryfi\nc=veryfi.Client()\nc.delete_w8(doc)'), False)
    def test_excluded_048(self):
        self.assertEqual(evidence('import mindee\nc=mindee.Client()\nc.parse(BankCheckV1, doc)'), False)
    def test_excluded_049(self):
        self.assertEqual(evidence('import mindee\nc=mindee.Client()\nc.parse(InvoiceV4, doc)'), False)
    def test_excluded_050(self):
        self.assertEqual(evidence('import mindee\nc=mindee.Client()\nc.parse(ReceiptV5, doc)'), False)
    def test_excluded_051(self):
        self.assertEqual(evidence('import mindee\nc=mindee.Client()\nc.parse(PassportV1, doc)'), False)
    def test_excluded_052(self):
        self.assertEqual(evidence('import mindee\nc=mindee.Client()\nc.parse(FinancialDocumentV1, doc)'), False)
    def test_excluded_053(self):
        self.assertEqual(evidence('import mindee\nc=mindee.Client()\nc.parse(BankAccountDetailsV2, doc)'), False)
    def test_excluded_054(self):
        self.assertEqual(evidence('import mindee\nc=mindee.Client()\nc.parse(CustomV1, doc)'), False)
    def test_excluded_055(self):
        self.assertEqual(evidence('import mindee\nc=mindee.Client()\nc.parse(TaxReturnV1, doc)'), False)
    def test_excluded_056(self):
        self.assertEqual(evidence('textract.analyze_document(doc)'), False)
    def test_excluded_057(self):
        self.assertEqual(evidence('textract.analyze_expense(doc)'), False)
    def test_excluded_058(self):
        self.assertEqual(evidence('textract.start_document_analysis(doc)'), False)
    def test_excluded_059(self):
        self.assertEqual(evidence('textract.get_expense_analysis(doc)'), False)
    def test_excluded_060(self):
        self.assertEqual(evidence('pdfplumber.extract_text(doc)'), False)
    def test_excluded_061(self):
        self.assertEqual(evidence('fitz.extract_text(doc)'), False)
    def test_excluded_062(self):
        self.assertEqual(evidence('pypdf.extract_text(doc)'), False)
    def test_excluded_063(self):
        self.assertEqual(evidence('PyPDF2.extract_text(doc)'), False)
    def test_excluded_064(self):
        self.assertEqual(evidence('pdfminer.extract_text(doc)'), False)
    def test_excluded_065(self):
        self.assertEqual(evidence('pytesseract.image_to_string(doc)'), False)
    def test_excluded_066(self):
        self.assertEqual(evidence('pandas.read_csv(doc)'), False)
    def test_excluded_067(self):
        self.assertEqual(evidence('pandas.read_excel(doc)'), False)
    def test_excluded_068(self):
        self.assertEqual(evidence('camelot.read_pdf(doc)'), False)
    def test_excluded_069(self):
        self.assertEqual(evidence('tabula.read_pdf(doc)'), False)
    def test_excluded_070(self):
        self.assertEqual(evidence('tabula.convert_into(doc)'), False)
    def test_excluded_071(self):
        self.assertEqual(evidence('pdfplumber.extract_table(doc)'), False)
    def test_excluded_072(self):
        self.assertEqual(evidence('pdfplumber.extract_tables(doc)'), False)
    def test_excluded_073(self):
        self.assertEqual(evidence('pdfplumber.find_table(doc)'), False)
    def test_excluded_074(self):
        self.assertEqual(evidence('pdfplumber.find_tables(doc)'), False)
    def test_excluded_075(self):
        self.assertEqual(evidence('fitz.find_tables(doc)'), False)
    def test_excluded_076(self):
        self.assertEqual(evidence('re.search("wages", text)\nfields={"wages": 1}'), False)
    def test_excluded_077(self):
        self.assertEqual(evidence('text="W-2"\nboxes=text.split()'), False)
    def test_excluded_078(self):
        self.assertEqual(evidence('subprocess.run(["veryfi", "w2s", "process", "doc"])'), False)
    def test_excluded_079(self):
        self.assertEqual(evidence('subprocess.run(["mindee", "parse", "doc"])'), False)
    def test_fence_0(self):
        self.assertEqual(claims('```\nextract tax forms\n```'), (False, False))
    def test_fence_1(self):
        self.assertEqual(claims('   ~~~~\nextract tax forms\n   ~~~~'), (False, False))
    def test_fence_2(self):
        self.assertEqual(claims('```text\nextract tax forms\n```'), (False, False))
    def test_inline_and_contraction(self):
        self.assertEqual(claims('We `extract tax forms`.'), (True, False))
        self.assertEqual(claims("doesn't extract tax forms"), (False, True))
        self.assertEqual(claims('tax-form extraction'), (True, False))
    def test_excluded_paths(self):
        self.put('README.md', 'extract tax forms')
        for path in ('fixtures/app.py', 'docs/app.py', 'examples/app.py'):
            self.put(path, 'x.extract_tax_form(doc)')
        self.assertEqual(self.cli()[0], 2)
    def test_test_filename(self):
        self.put('README.md', 'extract tax forms')
        self.put('app_test.py', 'x.extract_tax_form(doc)')
        self.assertEqual(audit(self.root)['findings'][0]['severity'], 'MEDIUM')

if __name__ == '__main__':
    unittest.main()
