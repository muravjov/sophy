import os
import shutil
import sys
import unittest

from sophy import Sophia


TEST_DIR = 'sophia-test'


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        if os.path.exists(TEST_DIR):
            shutil.rmtree(TEST_DIR)
        self.db = self.create_db()
        self.db.open()

    def tearDown(self):
        self.db.close()
        if os.path.exists(TEST_DIR):
            shutil.rmtree(TEST_DIR)

    def create_db(self):
        raise NotImplementedError


class TestSophia(BaseTestCase):
    def create_db(self):
        return Sophia('test-kv', path=TEST_DIR)

    def test_version(self):
        v = self.db.version
        self.assertEqual(v, '1.2.3')

    def test_kv(self):
        self.db['k1'] = 'v1'
        self.assertEqual(self.db['k1'], 'v1')

        self.db['k1'] = 'v1-e'
        self.assertEqual(self.db['k1'], 'v1-e')

        del self.db['k1']
        self.assertRaises(KeyError, lambda: self.db['k1'])
        self.assertEqual(len(self.db), 0)

        self.db['k2'] = 'v2'
        self.db['k3'] = 'v3'

        self.assertFalse('k1' in self.db)
        self.assertTrue('k2' in self.db)

        self.assertEqual(len(self.db), 2)

    def test_collections(self):
        self.db['k1'] = 'v1'
        self.db['k2'] = 'v2'
        self.db['k3'] = 'v3'

        self.assertEqual(list(self.db.keys()), ['k1', 'k2', 'k3'])
        self.assertEqual(list(self.db.values()), ['v1', 'v2', 'v3'])
        self.assertEqual(list(self.db.items()), [
            ('k1', 'v1'),
            ('k2', 'v2'),
            ('k3', 'v3')])

        self.assertEqual(len(self.db), 3)

        self.assertEqual(list(self.db), list(self.db.items()))

    def test_update(self):
        self.db.update(k1='v1', k2='v2', k3='v3')
        self.assertEqual(list(self.db.items()), [
            ('k1', 'v1'),
            ('k2', 'v2'),
            ('k3', 'v3')])

        self.db.update({'k1': 'v1-e', 'k3': 'v3-e', 'k4': 'v4'})
        self.assertEqual(list(self.db.items()), [
            ('k1', 'v1-e'),
            ('k2', 'v2'),
            ('k3', 'v3-e'),
            ('k4', 'v4')])

    def test_txn(self):
        self.db['k1'] = 'v1'
        self.db['k2'] = 'v2'
        with self.db.transaction() as txn:
            self.assertEqual(txn['k1'], 'v1')
            txn['k1'] = 'v1-e'
            del txn['k2']
            txn['k3'] = 'v3'

        self.assertEqual(self.db['k1'], 'v1-e')
        self.assertRaises(KeyError, lambda: self.db['k2'])
        self.assertEqual(self.db['k3'], 'v3')

    def test_rollback(self):
        self.db['k1'] = 'v1'
        self.db['k2'] = 'v2'
        with self.db.transaction() as txn:
            self.assertEqual(txn['k1'], 'v1')
            txn['k1'] = 'v1-e'
            del txn['k2']
            txn.rollback()
            txn['k3'] = 'v3'

        self.assertEqual(self.db['k1'], 'v1')
        self.assertEqual(self.db['k2'], 'v2')
        self.assertEqual(self.db['k3'], 'v3')

    def test_wb(self):
        self.db['k1'] = 'v1'
        self.db['k2'] = 'v2'
        with self.db.batch() as wb:
            self.assertRaises(Exception, lambda: wb['k1'])
            wb['k1'] = 'v1-e'
            del wb['k2']
            wb['k3'] = 'v3'

        self.assertEqual(self.db['k1'], 'v1-e')
        self.assertRaises(KeyError, lambda: self.db['k2'])
        self.assertEqual(self.db['k3'], 'v3')

    def test_cursor(self):
        for i in range(3):
            self.db['k%s' % i] = 'v%s' % i

        curs = self.db.cursor()
        self.assertEqual(
            list(curs),
            [('k0', 'v0'), ('k1', 'v1'), ('k2', 'v2')])

        curs = self.db.cursor(order='<')
        self.assertEqual(
            list(curs),
            [('k2', 'v2'), ('k1', 'v1'), ('k0', 'v0')])

    def test_key(self):
        self.db['aa'] = 'v1'
        self.db['ab'] = 'v2'
        self.db['aab'] = 'v3'
        self.db['abb'] = 'v4'
        self.db['bab'] = 'v5'
        self.db['baa'] = 'v6'

        curs = self.db.cursor(key='ab')
        self.assertEqual(list(curs), [
            ('ab', 'v2'),
            ('abb', 'v4'),
            ('baa', 'v6'),
            ('bab', 'v5'),
        ])

        curs = self.db.cursor(key='abb', order='<')
        self.assertEqual(list(curs), [
            ('ab', 'v2'),
            ('aab', 'v3'),
            ('aa', 'v1'),
        ])

        curs = self.db.cursor(key='c')
        self.assertEqual(list(curs), [])

        curs = self.db.cursor(key='a', order='<')
        self.assertEqual(list(curs), [])

    def test_prefix(self):
        self.db['aaa'] = '1'
        self.db['aab'] = '2'
        self.db['aba'] = '3'
        self.db['abb'] = '4'
        self.db['baa'] = '5'

        curs = self.db.cursor(order='>=', prefix='a')
        self.assertEqual(list(curs), [
            ('aaa', '1'),
            ('aab', '2'),
            ('aba', '3'),
            ('abb', '4')])

        curs = self.db.cursor(order='>=', prefix='ab')
        self.assertEqual(list(curs), [
            ('aba', '3'),
            ('abb', '4')])


if __name__ == '__main__':
    unittest.main(argv=sys.argv)