# Guion de demostración · V2

**Tema completo:** Reconocimiento y clasificación automatizada de documentos mediante modelos de visión artificial y agentes de IA.

> La prioridad es enseñar a utilizar el conocimiento de ingeniería para elegir una solución. OCR y reglas donde son suficientes; modelos de imagen en Python para rasgos visuales; agentes bajo autorización y presupuesto para excepciones.

## Secuencia sugerida (6–10 minutos de demo)

1. Desde la raíz: `python -m pytest -q` (9 tests automatizados sin AWS ni API).
2. `python run_demo.py --source local --path samples` → 11 PDFs ficticios, 3 clasificados, 2 descartados, 6 pendientes, 0 llamadas IA.
3. `python run_demo.py --source local --path samples --ocr --ocr-lang eng` → 4 clasificados, 2 descartados, 5 pendientes, 0 llamadas IA. La diferencia es una página escaneada reconocida por OCR.
4. `streamlit run app.py`: muestra visualmente los ejemplos escaneados; activa/desactiva OCR y visión HOG+SVM. **El margen del SVM no es una probabilidad** y no valida documentos reales.
5. Abre pestaña **Escenario hipotético: 50.000** y modifica los supuestos. Señala que **no** es un benchmark ni se ha procesado ese volumen.
6. Abre **Prompt + Skill**; explica qué es `skills/reconocimiento_idpr/SKILL.md`, cómo el programa lo integra al prompt de sistema y cómo impone un JSON schema.
7. El agente está desactivado por defecto. Solo usarlo con consentimiento, documentos autorizados y un modelo/clave API disponible. No necesitamos hacer una llamada pagada para demostrar la arquitectura.

## Momento para preguntas

- Diapositiva 19: ¿qué técnica usarías primero en una página clara, una foto inclinada y una imagen borrosa?
- Diapositiva 28: ¿cuándo sí vale la pena consultar al agente? Considera incertidumbre, recaptura, costo y privacidad.

## Fórmula que puedes explicar verbalmente

**HIPOTÉTICO:** 50.000 = 32.500 reglas/OCR + 13.000 visión+ML + 3.000 IA + 1.500 humanos.
Si cada llamada supuesta cuesta 2.020 tokens: 3.000 × 2.020 = 6.060.000 tokens.
Si todos fueran a IA: 50.000 × 2.020 = 101.000.000 tokens.
**94% de llamadas evitadas** en esta simulación, no un ahorro de dinero medido.

## Precauciones

- Ningún documento del demo es real. Las credenciales son ficticias, no tienen valor oficial ni sirven para comprobar identidad.
- HOG+SVM aprende solo de 90 dibujos sintéticos; no hay precisión validada de producción.
- El agente es una llamada multimodal dirigida, sin herramientas de ejecución autónoma.
- Nunca presentar una respuesta del agente o score del modelo como identificación personal confirmada.
- El demo lee S3 pero no escribe, renombra ni borra archivos.

La explicación extensa de **las 34 diapositivas** está en la guía DOCX entregada junto al PowerPoint.
