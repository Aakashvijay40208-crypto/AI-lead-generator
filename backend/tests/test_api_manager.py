import unittest
import os
import api_manager

class TestApiManager(unittest.TestCase):
    def setUp(self):
        # Override key_metrics for clean testing environment
        api_manager.key_metrics = {
            "outscraper": {"keys": ["key_o1", "key_o2"], "index": 0, "usage": {"key_o1": 0, "key_o2": 0}, "disabled": set()},
            "gemini": {"keys": ["key_g1"], "index": 0, "usage": {"key_g1": 0}, "disabled": set()},
            "openai": {"keys": [], "index": 0, "usage": {}, "disabled": set()}
        }
        
    def test_key_rotation_round_robin(self):
        # First call rotates
        key_first = api_manager.get_api_key("outscraper")
        key_second = api_manager.get_api_key("outscraper")
        key_third = api_manager.get_api_key("outscraper")
        
        self.assertIn(key_first, ["key_o1", "key_o2"])
        self.assertIn(key_second, ["key_o1", "key_o2"])
        self.assertNotEqual(key_first, key_second)
        
        # Third call should loop back
        self.assertEqual(key_third, key_first)
        
    def test_disable_failed_key(self):
        # Disable key_o1
        api_manager.disable_key("outscraper", "key_o1")
        
        # Now it should only return key_o2
        key1 = api_manager.get_api_key("outscraper")
        key2 = api_manager.get_api_key("outscraper")
        
        self.assertEqual(key1, "key_o2")
        self.assertEqual(key2, "key_o2")
        
    def test_empty_provider_fallback(self):
        # OpenAI has no keys, should return None
        key = api_manager.get_api_key("openai")
        self.assertIsNone(key)
        
    def test_reset_metrics(self):
        api_manager.disable_key("outscraper", "key_o1")
        api_manager.get_api_key("outscraper")
        
        api_manager.reset_metrics()
        
        self.assertEqual(len(api_manager.key_metrics["outscraper"]["disabled"]), 0)
        self.assertEqual(api_manager.key_metrics["outscraper"]["usage"]["key_o1"], 0)

if __name__ == "__main__":
    unittest.main()
