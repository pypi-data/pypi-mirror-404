import unittest
from ttsign_mobile import ttsign_mobile

class TestTTSignMobile(unittest.TestCase):
    def test_basic_signature(self):
        """Test basic signature generation"""
        signer = ttsign_mobile(
            params="test=value",
            data='{"key": "data"}',
            cookies="session=abc123"
        )
        
        result = signer.get_value()
        
        self.assertIn("x-ss-req-ticket", result)
        self.assertIn("x-khronos", result)
        self.assertIn("x-gorgon", result)
        
        self.assertTrue(result["x-gorgon"].startswith("0404b0d30000"))
    
    def test_empty_data_and_cookies(self):
        """Test with empty data and cookies"""
        signer = ttsign_mobile(
            params="test=value",
            data="",
            cookies=""
        )
        
        result = signer.get_value()
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 3)

if __name__ == "__main__":
    unittest.main()
