# Aviso de privacidad y alcance del demo V4

- Las **tres muestras originales** cargadas por el usuario (CE.pdf, IDPR.pdf y CA.pdf) **NO** se incluyen en el ZIP.
- Los cinco archivos `samples/12–16_*.pdf` fueron **recreados desde cero**, únicamente a partir de rasgos públicos del formato, y contienen campos ficticios.
- Las imágenes del directorio `assets/muestras_v3/` también son generadas desde cero; no son redacciones reversibles.
- CE: certificación de instalación eléctrica. CA: contrato de venta al por menor a plazos (CA.pdf es un documento de 40 páginas y contiene esa portada en la página 2). IDPR: tarjeta de identificación de Puerto Rico.
- Las escenas difíciles son manipulaciones sintéticas de dichas recreaciones.
- **No compartir los originales** ni probar un proveedor cloud sobre datos reales sin autorización.
- HOG+SVM y TF-IDF usan datos sintéticos; ni márgenes ni similitudes demuestran precisión o autenticidad.
- S3 debe usar credenciales IAM limitadas a ListBucket condicionado al prefijo y GetObject sólo del prefijo, nunca permisos de escritura.
- La validación de llamadas y datos externos debe hacerse en código, no confiar exclusivamente en un prompt o Skill.
