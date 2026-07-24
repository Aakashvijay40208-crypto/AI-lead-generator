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
        audit = {
            "website_status": 0,
            "is_https": False,
            "response_time_ms": 0,
            "seo": {"title": "", "description": ""},
            "ux": {"isMobileFriendly": False},
            "tech_detected": {"whatsapp": False, "bookingSystem": False}
        }
        
        result = calculate_lead_score(business, audit)
        
        # Capped at 100, but logic checks:
        # No website (+40), No SEO (+20), No SSL (+10), Not mobile friendly (+10), No whatsapp (+10), No booking (+5) = 95.
        self.assertEqual(result["score"], 95)
        self.assertEqual(result["priority"], "HOT")
        self.assertIn("No Website", result["failed_checks"])
        
    def test_perfect_website(self):
        # Business with a fast, secure website containing WhatsApp, booking, etc.
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
            "ux": {"isMobileFriendly": True, "hasHeroSection": True},
            "tech_detected": {"whatsapp": True, "bookingSystem": True, "crm": True},
            "contacts": {"emails": ["contact@perfect.com"]}
        }
        
        ai_analysis = {
            "problems_detected": {
                "outdated_design": False,
                "old_website": False,
                "broken_contact_form": False
            }
        }
        
        result = calculate_lead_score(business, audit, ai_analysis)
        
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["priority"], "LOW")
        self.assertEqual(len(result["failed_checks"]), 0)
        
    def test_some_deficiencies(self):
        # Has website, but lacks SSL, SEO title, WhatsApp and is slow
        business = {
            "place_id": "test_place_deficiencies",
            "name": "Medium Shop",
            "website": "http://medium.com" # HTTP -> No SSL
        }
        audit = {
            "website_status": 200,
            "is_https": False,
            "response_time_ms": 4000, # >3s -> Slow performance (+10)
            "seo": {"title": "", "description": ""}, # Missing SEO (+20)
            "ux": {"isMobileFriendly": True},
            "tech_detected": {"whatsapp": False, "bookingSystem": False} # No whatsapp (+10), No booking (+5)
        }
        
        # HTTP (+10) + Slow (+10) + SEO (+20) + Whatsapp (+10) + Booking (+5) = 55
        result = calculate_lead_score(business, audit)
        
        self.assertEqual(result["score"], 55)
        self.assertEqual(result["priority"], "MEDIUM")
        self.assertIn("No SSL (Not HTTPS)", result["failed_checks"])
        self.assertIn("Poor Performance (Page load > 3s)", result["failed_checks"])

if __name__ == "__main__":
    unittest.main()
