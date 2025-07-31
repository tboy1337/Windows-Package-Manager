import unittest
import os
import tempfile
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.app_database import AppDatabase

class TestAppDatabase(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False).name
        self.db = AppDatabase(self.temp_db)

    def tearDown(self):
        self.db.conn.close()
        os.unlink(self.temp_db)

    def test_create_tables(self):
        # Tables should be created without error
        self.db.create_tables()  # Call again to test idempotency
        self.assertTrue(True)  # No exception

    def test_save_profile_new(self):
        self.db.save_profile('test', ['id1', 'id2'])
        loaded = self.db.load_profile('test')
        self.assertEqual(loaded, ['id1', 'id2'])

    def test_save_profile_update(self):
        self.db.save_profile('test', ['id1'])
        self.db.save_profile('test', ['id3', 'id4'])
        loaded = self.db.load_profile('test')
        self.assertEqual(loaded, ['id3', 'id4'])

    def test_load_profile_nonexistent(self):
        loaded = self.db.load_profile('nonexistent')
        self.assertEqual(loaded, [])

    def test_get_all_profiles(self):
        self.db.save_profile('profile1', [])
        self.db.save_profile('profile2', [])
        profiles = self.db.get_all_profiles()
        self.assertIn('profile1', profiles)
        self.assertIn('profile2', profiles)
        self.assertEqual(len(profiles), 2)

    def test_delete_profile(self):
        self.db.save_profile('test', ['id1'])
        self.db.delete_profile('test')
        loaded = self.db.load_profile('test')
        self.assertEqual(loaded, [])
        profiles = self.db.get_all_profiles()
        self.assertNotIn('test', profiles)

if __name__ == '__main__':
    unittest.main()
