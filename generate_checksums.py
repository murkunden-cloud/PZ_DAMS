import hashlib
import os
import json

def generate_checksums(file_path):
    """Generate SHA256 and MD5 checksums for a file"""
    sha256_hash = hashlib.sha256()
    md5_hash = hashlib.md5()
    
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
            md5_hash.update(chunk)
    
    return {
        "sha256": sha256_hash.hexdigest(),
        "md5": md5_hash.hexdigest(),
        "size": os.path.getsize(file_path)
    }

def create_server_checksums(exe_path, output_path="checksums.json"):
    """Create checksums.json for the update server"""
    if not os.path.exists(exe_path):
        print(f"Error: File not found: {exe_path}")
        return False
    
    checksums = {
        "DAMS.exe": generate_checksums(exe_path)
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=4)
    
    print(f"Checksums generated successfully: {output_path}")
    print(f"SHA256: {checksums['DAMS.exe']['sha256']}")
    print(f"MD5: {checksums['DAMS.exe']['md5']}")
    print(f"Size: {checksums['DAMS.exe']['size']} bytes")
    
    return True

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python generate_checksums.py <path_to_DAMS.exe> [output_json_path]")
        print("Example: python generate_checksums.py dist/DAMS/DAMS.exe")
        sys.exit(1)
    
    exe_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "checksums.json"
    
    create_server_checksums(exe_path, output_path)
