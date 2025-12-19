
import google.generativeai as genai
import os

api_key = "AIzaSyApmiL5_jph_lHGMGy_QzZ32voIacNW69s"
genai.configure(api_key=api_key)

print("--- Checking Available Models ---")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Name: {m.name}")
except Exception as e:
    print(f"Error connecting to Google: {e}")