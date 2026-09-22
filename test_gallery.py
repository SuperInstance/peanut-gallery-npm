"""Tests for the peanut gallery."""
import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from gallery import (
    PeanutGallery, GalleryCell, fnv1a_64,
    call_llm, call_jev,
)


class TestFNV1a(unittest.TestCase):
    def test_fleet_canary(self):
        self.assertEqual(fnv1a_64('café Δ 日本語'), '0x24a555471370b18d')


class TestGalleryCell(unittest.TestCase):
    def test_creation(self):
        cell = GalleryCell(
            cell_id='gallery-01',
            round_num=1,
            producer='qwen',
        )
        self.assertEqual(cell.round_num, 1)
        self.assertEqual(cell.prev_hash, '0x0000000000000000')
    
    def test_hash_changes(self):
        c1 = GalleryCell('g1', 1, 'qwen', output='hello')
        c2 = GalleryCell('g2', 2, 'qwen', output='world')
        self.assertNotEqual(c1.hash(), c2.hash())


class TestPeanutGallery(unittest.TestCase):
    def test_creation(self):
        g = PeanutGallery(prompt='test')
        self.assertEqual(g.producer, 'qwen')
        self.assertEqual(g.critics, ('deepseek', 'kimi', 'groq'))
        self.assertEqual(g.max_rounds, 5)
    
    def test_initial_round(self):
        g = PeanutGallery(prompt='test', max_rounds=1)
        cell = g._initial_producer_round(1, '0x0')
        self.assertEqual(cell.round_num, 1)
        self.assertIn('round_type', cell.metadata)
        self.assertEqual(cell.metadata['round_type'], 'initial')


if __name__ == '__main__':
    unittest.main(verbosity=2)
