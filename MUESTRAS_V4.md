# Muestras visuales incluidas en V4

## Procedencia y seguridad
Las tres estructuras visuales de ejemplo corresponden a formatos CE (certificación de instalación eléctrica), IDPR (identificación de Puerto Rico) y CA (contrato de venta al por menor a plazos) observados en archivos proporcionados por el usuario. **Todas las imágenes y archivos PDF V4 fueron recreados DESDE CERO con texto y elementos gráficos inventados**. No son PDF redacted reversibles ni incorporan una sola página original. No contienen datos personales reales, fotografía real, firmas reales, números de identificaciones originales ni metadatos de los PDF adjuntados.

## Archivos
- `samples/12_CE_recreado_anonimizado.pdf` — OCR + reglas, si OCR está activado.
- `samples/13_CA_venta_plazos_recreado_anonimizado.pdf` — contrato de venta a plazos; OCR + reglas.
- `samples/14_IDPR_recreado_anonimizado.pdf` — tarjeta ficticia; OCR + señales + TF-IDF.
- `samples/15_IDPR_mala_calidad_recreado.pdf` — deteriorado artificialmente; revisión pendiente.
- `samples/16_CE_escaneado_dificil_recreado.pdf` — deteriorado; revisión pendiente esperada.

Se incluyen tres formatos visuales recreados en `assets/muestras_v3`; la V4 no contiene memes.

## Alcance de los modelos
HOG + LinearSVC usa ilustraciones sintéticas entrenadas localmente, distintas a estos PDFs de V4. El margen SVM no es probabilidad calibrada. El clasificador no autentica identidades ni documentos. El modelo de IA generativa es opt-in y necesita clave y autorización explícita.
