import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from sentinel.core import assess, atomic_json, compare, read_json, validate_schema
from sentinel.__main__ import main
from sentinel.report import render_report

class SentinelTests(unittest.TestCase):
    def test_categories(self):
        changes = compare({'a':'INT','b':'TEXT'}, {'b':'INT','c':'TEXT'})
        self.assertEqual([(c['field'],c['kind']) for c in changes], [('a','removed'),('b','type_changed'),('c','added')])
        self.assertEqual([c['severity'] for c in changes], ['high','high','info'])

    def test_type_case(self):
        self.assertEqual(compare({'a':' int '}, {'a':'INT'}), [])

    def test_empty_schema(self):
        self.assertEqual(len(compare({'a':'INT','b':'TEXT'}, {})), 2)

    def test_invalid_schema(self):
        for schema in [[], {'a':None}, {'':'INT'}, {'a':' '}]:
            with self.subTest(schema=schema), self.assertRaises(ValueError):
                validate_schema(schema)

    def test_incident_lifecycle(self):
        state = {}; baseline = {'a':'INT'}; changed = {'a':'TEXT'}
        first = assess('x',baseline,changed,state)['changes'][0]
        repeat = assess('x',baseline,changed,state)['changes'][0]
        recovery = assess('x',baseline,baseline,state)
        returned = assess('x',baseline,changed,state)['changes'][0]
        self.assertEqual((first['occurrences'],first['newly_opened']), (1,True))
        self.assertEqual((repeat['occurrences'],repeat['newly_opened']), (1,False))
        self.assertEqual(recovery['resolved'], 1)
        self.assertEqual((returned['occurrences'],returned['newly_opened']), (2,True))

    def test_scope(self):
        state = {}; assess('x',{'a':'INT'},{},state)
        self.assertEqual(assess('y',{'a':'INT'},{},state)['changes'][0]['occurrences'],1)
        self.assertEqual(assess('x',{'a':'TEXT'},{},state)['changes'][0]['occurrences'],1)

    def test_new_type_transition(self):
        state = {}; assess('x',{'a':'INT'},{'a':'TEXT'},state)
        result = assess('x',{'a':'INT'},{'a':'FLOAT'},state)
        self.assertEqual(result['resolved'],1)
        self.assertEqual(result['changes'][0]['occurrences'],1)

    def test_addition_status(self):
        self.assertEqual(assess('x',{}, {'a':'INT'}, {})['status'],'review')

    def test_html_escaping(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'report.html'
            render_report(assess('<script>',{}, {'<img>':'TEXT'}, {}, ['<iframe>']),path)
            html = path.read_text()
            self.assertNotIn('<script>',html)
            self.assertNotIn('<iframe>',html)
            self.assertIn('&lt;img&gt;',html)

    def test_cli_lifecycle(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            root = Path(directory); baseline=root/'b.json'; current=root/'c.json'; output=root/'r.json'
            atomic_json(baseline,{'a':'INT'}); atomic_json(current,{})
            args=['check','--baseline',str(baseline),'--schema',str(current),'--dataset','x',
                  '--state',str(root/'state.json'),'--output',str(output),'--html',str(root/'r.html'),'--fail-on-breaking']
            self.assertEqual(main(args),2)
            self.assertTrue((root/'r.html').exists())
            self.assertEqual(main(args),2)
            self.assertFalse(read_json(output)['changes'][0]['newly_opened'])
            atomic_json(current,{'a':'INT'})
            self.assertEqual(main(args),0)
            self.assertEqual(read_json(output)['resolved'],1)

    def test_snapshot_guard(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            source=Path(directory)/'s.json'; target=Path(directory)/'b.json'
            atomic_json(source,{'a':'INT'})
            args=['snapshot','--schema',str(source),'--baseline',str(target)]
            self.assertEqual(main(args),0)
            atomic_json(source,{'a':'TEXT'})
            self.assertEqual(main(args),1)
            self.assertEqual(read_json(target),{'a':'INT'})
            self.assertEqual(main(args+['--overwrite']),0)

    def test_path_collision(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stderr(io.StringIO()):
            path=Path(directory)/'b.json'; atomic_json(path,{'a':'INT'})
            self.assertEqual(main(['check','--baseline',str(path),'--schema',str(path),'--dataset','x','--output',str(path)]),1)
            self.assertEqual(read_json(path),{'a':'INT'})

    def test_malformed_json(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stderr(io.StringIO()):
            path=Path(directory)/'bad.json'; path.write_text('{')
            self.assertEqual(main(['snapshot','--schema',str(path),'--baseline',str(Path(directory)/'out.json')]),1)

if __name__ == '__main__':
    unittest.main()
