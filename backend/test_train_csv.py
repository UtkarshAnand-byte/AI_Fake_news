import urllib.request
import urllib.error
import mimetypes

url = "http://127.0.0.1:8000/api/train?use_feedback=true"

# Construct simple CSV content
csv_content = """text,label
"This is a real news story about science.",0
"Shocking miracle cure exposed by anonymous source!",1
"NASA reports discovery of new water-bearing asteroid.",0
"Conspiracy theories about moon replacement are fake.",1
"""

# Format as multipart/form-data
boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
body = []
body.append(f"--{boundary}".encode('utf-8'))
body.append(f'Content-Disposition: form-data; name="file"; filename="train_data.csv"'.encode('utf-8'))
body.append(b'Content-Type: text/csv')
body.append(b'')
body.append(csv_content.encode('utf-8'))
body.append(f"--{boundary}--".encode('utf-8'))
body.append(b'')

payload = b'\r\n'.join(body)

print("Testing model retraining with a custom CSV dataset...")
try:
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        print("Success! Status:", resp.status)
        print("Response:", resp.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print("HTTPError! Status:", e.code)
    print("Response:", e.read().decode('utf-8'))
except Exception as e:
    print("Error:", e)
