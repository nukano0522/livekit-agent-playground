#!/usr/bin/env python3
import sounddevice as sd
import sys

print("=== Audio Device Check ===")
print()

try:
    # デバイス一覧を取得
    devices = sd.query_devices()
    
    if not devices:
        print("No audio devices found.")
        print("This is expected in WSL2 environment without audio passthrough.")
    else:
        print(f"Found {len(devices)} device(s):")
        print()
        
        for i, device in enumerate(devices):
            print(f"Device #{i}: {device['name']}")
            print(f"  Host API: {device['hostapi']}")
            print(f"  Input channels: {device['max_input_channels']}")
            print(f"  Output channels: {device['max_output_channels']}")
            print(f"  Default sample rate: {device['default_samplerate']}")
            print()
            
    # デフォルトデバイスの確認
    print("Default devices:")
    try:
        default_input = sd.default.device[0]
        default_output = sd.default.device[1]
        print(f"  Input: {default_input}")
        print(f"  Output: {default_output}")
    except Exception as e:
        print(f"  Could not get default devices: {e}")
        
except Exception as e:
    print(f"Error querying devices: {e}")
    print(f"Error type: {type(e).__name__}")
    
print()
print("=== System Info ===")
print(f"Python version: {sys.version}")
print(f"sounddevice version: {sd.__version__}")

# PortAudioの情報
try:
    import sounddevice._portaudio as pa
    print(f"PortAudio version: {pa.get_version_text()}")
except:
    print("PortAudio version info not available")