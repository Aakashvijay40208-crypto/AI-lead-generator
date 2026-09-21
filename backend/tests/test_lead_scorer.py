import unittest
from lead_scorer import calculate_lead_score

class TestLeadScorer(unittest.TestCase):
    def test_no_website(self):
        # Business with no website
        business = {
            "place_id": "test_place_no_web",
            "name": "No Website Shop",
            "website": ""
        }
        
        result = calculate_lead_score(business)
        
        self.assertEqual(result["score"], 100)
        self.assertEqual(result["priority"], "HOT")
        self.assertEqual(result["website_status"], "No Website")
        self.assertIn("No Website", result["failed_checks"])
        
    def test_perfect_website(self):
        # Business with a fast, secure website
        business = {
            "place_id": "test_place_perfect",
            "name": "Perfect Shop",
            "website": "https://perfect.com"
        }
        audit = {
            "website_status": 200,
            "is_https": True,
            "response_time_ms": 500,
            "seo": {"title": "Perfect Shop - Home", "description": "Welcome to our shop"},
            "ux": {"isMobileFriendly": True}
        }
        
        result = calculate_lead_score(business, audit)
        
        self.assertEqual(result["score"], 30)
        self.assertEqual(result["priority"], "LOW")
        self.assertEqual(result["website_status"], "Website Available")
        self.assertEqual(len(result["failed_checks"]), 0)
        
    def test_some_deficiencies(self):
        # Has website, but lacks SSL, SEO title, and is slow
        business = {
            "place_id": "test_place_deficiencies",
            "name": "Medium Shop",
            "website": "http://medium.com" # HTTP -> No SSL (+15)
        }
        audit = {
            "website_status": 200,
            "is_https": False,
            "response_time_ms": 4000, # >3s -> Slow (+10)
            "seo": {"title": "", "description": ""}, # Missing SEO (+15)
            "ux": {"isMobileFriendly": True}
        }
        
        # Base (30) + SSL (+15) + SEO (+15) + Slow (+10) = 70 -> MEDIUM
        result = calculate_lead_score(business, audit)
        
        self.assertEqual(result["score"], 70)
        self.assertEqual(result["priority"], "MEDIUM")
        self.assertEqual(result["website_status"], "Website Available")
        self.assertIn("No SSL (Not HTTPS)", result["failed_checks"])
        self.assertIn("Slow Load Time (> 3s)", result["failed_checks"])

if __name__ == "__main__":
    unittest.main()

