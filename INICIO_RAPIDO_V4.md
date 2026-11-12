# Demo V4 — Inicio rápido

1. Requiere Python 3.10+ (recomendado 3.11), una terminal y un entorno virtual.
2. Ejecuta `pip install -r requirements.txt`.
3. Ejecuta `streamlit run app.py`.
4. Selecciona **Muestras incluidas** y activa **OCR local (Tesseract)**. Para OCR instala Tesseract en el sistema, además de `pytesseract` de requirements.
5. Haz clic en **Ejecutar pipeline V4**. Revisa especialmente archivos `12_..16_`: CE, CA e IDPR se distinguen con OCR; los dos degradados ilustran abstención.
6. Abre **Escenario hipotético: 50.000** y **Prompt + Skill**. La simulación no es medición real.

En Windows Tesseract debe quedar en el PATH. Puedes usar `eng` como idioma OCR si no tienes `spa` instalado.

**Privacidad:** todas las muestras V4 son recreaciones nuevas y totalmente ficticias. Los originales proporcionados por el usuario no están incluidos en este paquete.

**Limitaciones:** S3 real requiere IAM de solo lectura y autorización; el proveedor LLM no está conectado ni probado en una cuenta real; el agente es opcional y puede generar cargos; el modelo HOG+SVM solo vio entrenamiento sintético, no tiene precisión validada con documentos reales.
