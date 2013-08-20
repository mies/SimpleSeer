import time
import unittest

import mock

from SimpleSeer import util

class Test(unittest.TestCase):

    @util.jsonify
    def _jsonified(self, x):
        return x

    @mock.patch('SimpleSeer.util.make_response')
    @mock.patch('SimpleSeer.util.jsonencode')
    def test_jsonify(self, jsonencode, make_response):
        make_response.return_value.headers = {}
        x = dict(a=5)
        result = self._jsonified(x)
        jsonencode.assert_called_with(x)
        make_response.assert_called_with(
            jsonencode.return_value, 200)
        self.assertEqual(result.headers['Content-Type'], 'application/json')

    @mock.patch('SimpleSeer.util.make_response')
    @mock.patch('SimpleSeer.util.jsonencode')
    def test_jsonify_none(self, jsonencode, make_response):
        self._jsonified(None)
        jsonencode.assert_called_with({})

    def test_convert_str(self):
        encoded = util.utf8convert('foo')
        assert isinstance(encoded, str)
        unicode(encoded, 'utf-8') # verify valid utf-8
        self.assertEqual(encoded, 'foo')

    def test_convert_unicode(self):
        encoded = util.utf8convert(u'foo\u0200')
        assert isinstance(encoded, str)
        unicode(encoded, 'utf-8') # verify valid utf-8
        self.assertEqual(encoded, 'foo\xc8\x80')

    def test_convert_dict(self):
        encoded = util.utf8convert({u'foo\u0200':'foo', 'bar': u'foo\u0200'})
        self.assertEqual(encoded, {
                'foo\xc8\x80':'foo', 'bar': 'foo\xc8\x80'})

    def test_convert_list(self):
        encoded = util.utf8convert([u'foo\u0200', 'bar'])
        self.assertEqual(encoded, ['foo\xc8\x80', 'bar'])
        
    def test_convert_other(self):
        class MyObject(object): pass
        x = MyObject()
        encoded = util.utf8convert(x)
        assert encoded is x

    def test_clock(self):
        c = util.Clock(100)
        start = time.time()
        a = None
        for x in range(20):
            c.tick()
            b = time.time()
            if a is not None:
                self.assertAlmostEqual(b-a, 0.01, delta=0.002)
            a = b
        elapsed = time.time() - start
        self.assertAlmostEqual(elapsed, 0.2, delta=0.01)
