import pytest
import json
from compressors.json_compressor import ToonConverter, JsonCompressor

class TestToonConverter:
    def test_simple_conversion(self):
        data = [
            {"name": "Alice", "role": "admin"},
            {"name": "Bob", "role": "user"}
        ]
        toon = ToonConverter.to_toon(data)
        # Check header
        assert "name|role" in toon or "role|name" in toon
        # Check values
        assert "Alice|admin" in toon
        assert "Bob|user" in toon
        
        # Roundtrip
        restored = ToonConverter.from_toon(toon)
        # Sort by name to ensure order for comparison
        data.sort(key=lambda x: x['name'])
        restored.sort(key=lambda x: x['name'])
        assert restored == data

    def test_nested_objects(self):
        data = [
            {"id": 1, "meta": {"foo": "bar"}},
            {"id": 2, "meta": {"foo": "baz"}}
        ]
        toon = ToonConverter.to_toon(data)
        
        # Roundtrip
        restored = ToonConverter.from_toon(toon)
        # Verify types
        assert restored[0]['id'] == 1
        assert restored[0]['meta'] == {"foo": "bar"}
        assert restored[1]['meta'] == {"foo": "baz"}

    def test_special_characters(self):
        data = [
            {"text": "Line 1\nLine 2", "code": "A|B"},
            {"text": "Simple", "code": "C"}
        ]
        toon = ToonConverter.to_toon(data)
        
        # Roundtrip verification is most important
        restored = ToonConverter.from_toon(toon)
        assert restored[0]['text'] == "Line 1\nLine 2"
        assert restored[0]['code'] == "A|B"

class TestJsonCompressor:
    def test_compress_flow(self):
        # A large repeated json structure
        data = []
        for i in range(10):
            data.append({
                "id": i,
                "description": "This is a very long description that is repeated many times to test compression efficiency."
            })
            
        result = JsonCompressor.compress(data, model="gpt-4")
        
        assert result['toon_conversion'] is True
        assert len(result['intermediate_toon']) < len(json.dumps(data))
        # Check that we have a dictionary from PCompressLR
        assert isinstance(result['dictionary'], dict)
        # The description should be compressed in the text (replaced by short ref)
        assert "This is a very long description" not in result['compressed_text']
        # But should be in the dictionary
        found_in_dict = False
        for k, v in result['dictionary'].items():
            if "This is a very long description" in v:
                found_in_dict = True
                break
        assert found_in_dict
