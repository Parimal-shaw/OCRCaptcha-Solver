import os
import tempfile
import subprocess


def extract_img(body):
    temp = tempfile.TemporaryFile(delete=False)
    try:
        temp.write(body)
        temp.seek(0)
        file_path = temp.name
    finally:
        temp.close()
    #provide path to the tesseract.exe below
    tesseract_cmd = "tesseract"
    command = [tesseract_cmd, file_path, "stdout"]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    value = stdout.decode('utf-8')
    os.remove(file_path)
    return value