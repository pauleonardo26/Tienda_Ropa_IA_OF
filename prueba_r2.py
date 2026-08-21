import os
import boto3
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
    "s3",
    endpoint_url=os.getenv("R2_ENDPOINT_URL"),
    aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
)

bucket = os.getenv("R2_BUCKET_NAME")


archivo_local = "Manga larga Gr Niña.png"
nombre_r2 = "productos/polo_nina_manga_larga_grande.png"

s3.upload_file(
    archivo_local,
    bucket,
    nombre_r2,
    ExtraArgs={"ContentType": "image/png"}
)

print("✅ Foto subida correctamente")
print("Archivo en R2:", nombre_r2)