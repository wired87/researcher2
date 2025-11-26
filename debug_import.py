import os
import sys

print("Python executable:", sys.executable)
print("Python path:", sys.path)

try:
    from google import genai
    print("Successfully imported google.genai")
except ImportError as e:
    print(f"Failed to import google.genai: {e}")
    sys.exit(1)

try:
    client = genai.Client(api_key="test")
    print("Successfully instantiated Client with dummy key")
except Exception as e:
    print(f"Failed to instantiate Client: {e}")
