"""Fuentes de sólo lectura. Una carpeta S3 es un prefix, no un directorio real."""
from __future__ import annotations
from pathlib import Path

MAX_PDF_BYTES = 12 * 1024 * 1024


def local_pdfs(folder: str, limit: int = 20):
    folder_path = Path(folder).expanduser().resolve()
    if not folder_path.exists() or not folder_path.is_dir():
        raise ValueError('Carpeta local inexistente')
    pdfs = sorted(p for p in folder_path.rglob('*') if p.is_file() and p.suffix.lower() == '.pdf')
    for pdf in pdfs[:limit]:
        if pdf.stat().st_size > MAX_PDF_BYTES:
            yield str(pdf.relative_to(folder_path)), None, 'Archivo mayor a 12 MB'
        else:
            yield str(pdf.relative_to(folder_path)), pdf.read_bytes(), None


def s3_pdfs(bucket: str, prefix: str, limit: int = 20, region: str = '', profile: str = ''):
    if not bucket.strip() or not prefix.strip().strip('/'):
        raise ValueError('Indica bucket y prefijo S3 no vacío (nunca apuntar a toda la raíz)')
    from boto3.session import Session
    session = Session(profile_name=profile.strip() or None, region_name=region.strip() or None)
    client = session.client('s3')
    prefix = prefix.lstrip('/')
    # Usa prefijo exacto introducido; para carpetas completa con / en el formulario.
    found = 0
    paginator = client.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix,
                                   PaginationConfig={'PageSize': 100}):
        for obj in page.get('Contents', []):
            key = obj['Key']
            if key.lower().endswith('.pdf') and not key.endswith('/'):
                found += 1
                if obj['Size'] > MAX_PDF_BYTES:
                    yield key, None, 'PDF mayor a 12 MB; omitido'
                else:
                    data = client.get_object(Bucket=bucket, Key=key)['Body'].read(MAX_PDF_BYTES + 1)
                    if len(data) > MAX_PDF_BYTES:
                        yield key, None, 'PDF excedió máximo de lectura'
                    else:
                        yield key, data, None
                if found >= limit:
                    return
