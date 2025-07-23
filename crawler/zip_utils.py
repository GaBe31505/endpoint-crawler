import zipfile
from crawler.io import read_bytes


def extract_java_from_zip(zip_path: str) -> list:
    pairs=[]
    try:
        with zipfile.ZipFile(zip_path) as z:
            for info in z.infolist():
                if info.filename.endswith('.java'):
                    raw=z.read(info.filename)
                    txt=read_bytes(raw)
                    pairs.append((f"{zip_path}!{info.filename}",txt))
    except zipfile.BadZipFile:
        pass
    return pairs