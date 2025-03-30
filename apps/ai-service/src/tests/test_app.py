# 각 모듈에 대한 단위 테스트
# tests/test_app.py
import unittest
from app import loaders, splitters, utils, virtual_db

class TestLoaders(unittest.TestCase):
    def test_load_pdf(self):
        # sample.pdf는 data/raw/에 있다고 가정합
        docs = loaders.load_pdf("data/raw/sample.pdf")
        self.assertTrue(len(docs) > 0)

class TestSplitters(unittest.TestCase):
    def test_split_text(self):
        text = "이것은 테스트 문장입니다. " * 100
        chunks = splitters.split_text(text, chunk_size=100, chunk_overlap=10)
        self.assertTrue(len(chunks) > 0)
        for chunk in chunks:
            self.assertTrue(len(chunk) <= 110)  # 100 + 10 overlap

class TestVirtualDB(unittest.TestCase):
    def test_load_virtual_db(self):
        db = virtual_db.load_virtual_db()
        self.assertIn("User", db)
        self.assertIn("Hotel", db)
        self.assertIn("Flight", db)
        self.assertIn("Reservation", db)
        self.assertIn("QueryLog", db)
        self.assertIn("AdminSettings", db)

if __name__ == '__main__':
    unittest.main()
