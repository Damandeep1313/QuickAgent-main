import ssl
import certifi

print("SSL Certificate Path:", certifi.where())
print("SSL Certificate Verification:", ssl.get_default_verify_paths())
