import unittest
import time
from tikdjoub import (
    sign, UserAgentTik, Gorgon, Ladon, 
    trace_id, md5stub, xor, Newparams, 
    host, ProtoBuf
)

class TestTikdjoub(unittest.TestCase):
    
    def test_sign_function(self):
        """Test main sign function"""
        headers = sign(
            params={"device_id": "123456", "aid": "1233"},
            data='{"test": "data"}',
            cookie="session=abc123"
        )
        
        self.assertIn("x-gorgon", headers)
        self.assertIn("x-ladon", headers)
        self.assertIn("x-argus", headers)
        self.assertIn("x-ss-stub", headers)
        self.assertIn("x-khronos", headers)
        self.assertIn("x-ss-req-ticket", headers)
    
    def test_user_agent(self):
        """Test UserAgentTik generation"""
        ua = UserAgentTik()
        self.assertIn("brand", ua)
        self.assertIn("type", ua)
        self.assertIn("User-Agent", ua)
        self.assertTrue(ua["User-Agent"].startswith("com.zhiliaoapp.musically/"))
    
    def test_gorgon_class(self):
        """Test Gorgon class"""
        g = Gorgon(
            params="test=123&aid=456",
            unix=1234567890,
            payload='{"action": "test"}',
            cookie="session=test"
        )
        
        result = g.get_value()
        self.assertIn("x-gorgon", result)
        self.assertIn("x-khronos", result)
        self.assertIn("x-ss-req-ticket", result)
    
    def test_ladon_class(self):
        """Test Ladon encryption"""
        ladon_str = Ladon.encrypt(
            x_khronos=1234567890,
            lc_id=1611921764,
            aid=1233
        )
        self.assertIsInstance(ladon_str, str)
        self.assertTrue(len(ladon_str) > 10)
    
    def test_trace_id(self):
        """Test trace_id generation"""
        trace = trace_id("device123")
        self.assertIsInstance(trace, str)
        self.assertTrue(trace.startswith("00-"))
    
    def test_md5stub(self):
        """Test md5stub function"""
        stub = md5stub("test data")
        self.assertIsInstance(stub, str)
        self.assertEqual(len(stub), 32)
    
    def test_xor(self):
        """Test xor function"""
        result = xor("test")
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 8)  # 4 chars * 2 hex digits
    
    def test_newparams(self):
        """Test Newparams function"""
        params = Newparams({"aid": "1233"})
        self.assertIn("_rticket", params)
        self.assertIn("device_id", params)
        self.assertIn("openudid", params)
        self.assertIn("ts", params)
    
    def test_host(self):
        """Test host selection"""
        api_host = host()
        self.assertIsInstance(api_host, str)
        self.assertTrue(len(api_host) > 0)
    
    def test_protobuf(self):
        """Test Protobuf encoding/decoding"""
        data = {"key": "value", "number": 123}
        pb = ProtoBuf(data)
        encoded = pb.toBuf()
        
        # Decode back
        pb2 = ProtoBuf(encoded)
        self.assertEqual(pb2[1], "value")
        self.assertEqual(pb2[2], 123)

if __name__ == "__main__":
    unittest.main()
