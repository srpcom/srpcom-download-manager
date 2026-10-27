import os
import base64
import hashlib
import json
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

def setup_extension_key():
    ext_dir = os.path.abspath("./browser_extension")
    pem_path = os.path.join(ext_dir, "key.pem")

    if not os.path.exists(pem_path):
        # Generate RSA 2048 private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        pem_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        with open(pem_path, "wb") as f:
            f.write(pem_bytes)
    else:
        with open(pem_path, "rb") as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None)

    # Get DER SubjectPublicKeyInfo
    public_key = private_key.public_key()
    der_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # Chrome Extension ID calculation:
    # First 128 bits (16 bytes) of SHA256 of the DER public key
    # Each byte's high nibble and low nibble mapped 0-15 -> 'a'-'p'
    sha = hashlib.sha256(der_bytes).digest()[:16]
    ext_id = "".join([chr(ord('a') + (b >> 4)) + chr(ord('a') + (b & 0x0F)) for b in sha])

    # Base64 string for manifest.json "key"
    b64_key = base64.b64encode(der_bytes).decode("ascii")

    # Update manifest.json
    manifest_path = os.path.join(ext_dir, "manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["key"] = b64_key

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Generated Chrome Extension ID: {ext_id}")
    return ext_id

if __name__ == "__main__":
    setup_extension_key()
