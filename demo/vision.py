"""Clasificador VISUAL de ejemplo: HOG + LinearSVC entrenado con imágenes sintéticas.

SIN identificaciones reales, SIN modelos preentrenados, SIN garantía de precisión.
Es un ejemplo didáctico de visión artificial con aprendizaje supervisado,
NO un verificador de documentos de identidad ni un método para autenticar personas.
"""
from __future__ import annotations
from dataclasses import dataclass
import io
import random
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
import numpy as np
from skimage.feature import hog
from sklearn.svm import LinearSVC

SHAPE = (160, 128)  # ancho, alto; todas las páginas a un espacio comparable


def _font(size=12):
    for path in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                 '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf'):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def _example_layout(label: int, seed: int) -> Image.Image:
    """Genera tarjetas/certificados ABSTRACTOS; texto deliberadamente ficticio."""
    rng = random.Random(seed)
    canvas = Image.new('RGB', (420, 540), (249, 250, 252))
    d = ImageDraw.Draw(canvas)
    x = rng.randint(34, 53)
    y = rng.randint(70, 102)
    if label == 1:
        # Tarjeta horizontal, no reproducción fiel de tarjeta gubernamental.
        cw, ch = rng.randint(310, 345), rng.randint(188, 212)
        d.rounded_rectangle((x, y, x+cw, y+ch), radius=14, fill=(213, 225, 233), outline=(72, 92, 109), width=3)
        d.rectangle((x+9, y+9, x+cw-9, y+42), fill=(70, 106, 136))
        d.text((x+17, y+17), 'TARJETA DEMO / IDPR', font=_font(14), fill='white')
        d.rectangle((x+18, y+67, x+96, y+144), fill=(159, 176, 181))
        d.ellipse((x+36, y+75, x+74, y+110), fill=(231, 232, 229))
        d.rectangle((x+32, y+118, x+83, y+140), fill=(231, 232, 229))
        for j in range(5):
            lw = rng.randint(110, 168)
            d.rectangle((x+119, y+68+j*20, x+119+lw, y+71+j*20), fill=(90, 112, 125))
        d.rectangle((x+16, y+ch-28, x+cw-18, y+ch-19), fill=(118, 139, 149))
    else:
        # Documento hoja A4 con título y líneas largas de texto.
        d.rectangle((x+7, y, x+332, y+400), fill='white', outline=(178, 190, 199), width=2)
        d.rectangle((x+32, y+32, x+271, y+44), fill=(103, 121, 133))
        for j in range(rng.randint(10, 14)):
            lw = rng.randint(135, 265)
            d.rectangle((x+31, y+86+j*20, x+31+lw, y+89+j*20), fill=(140, 155, 161))
        d.rectangle((x+30, y+352, x+160, y+354), fill=(111, 120, 128))
    if seed % 3 == 0:
        canvas = canvas.rotate(rng.uniform(-5, 5), expand=False, fillcolor=(252, 252, 252))
    if seed % 4 == 0:
        canvas = canvas.filter(ImageFilter.GaussianBlur(rng.uniform(.4, 1.1)))
    if seed % 5 == 0:
        canvas = ImageEnhance.Contrast(canvas).enhance(rng.uniform(.68, .95))
    return canvas


def _features(image: Image.Image) -> np.ndarray:
    # HOG observa bordes, gradientes y disposición espacial, NO entiende el texto.
    from PIL import ImageOps
    image = ImageOps.exif_transpose(image).convert('L').resize(SHAPE, Image.Resampling.BILINEAR)
    image = ImageOps.autocontrast(image)
    data = np.asarray(image, dtype=np.float32) / 255.0
    feature = hog(data, orientations=9, pixels_per_cell=(16, 16),
                  cells_per_block=(2, 2), block_norm='L2-Hys', feature_vector=True)
    return np.asarray(feature, dtype=np.float32)


@dataclass
class VisionScore:
    margin: float
    candidate: bool
    method: str = 'HOG + SVM lineal'


class SyntheticVisionModel:
    """SVM separador de ejemplos ARTIFICIALES; NO probabilidades calibradas."""
    def __init__(self, n_per_class: int = 45):
        data, labels = [], []
        for label in (0, 1):
            for i in range(n_per_class):
                data.append(_features(_example_layout(label, i+123*label)))
                labels.append(label)
        self.model = LinearSVC(C=0.6, random_state=42, max_iter=2500)
        self.model.fit(np.stack(data), np.array(labels))

    def score(self, image: Image.Image) -> VisionScore:
        margin = float(self.model.decision_function([_features(image)])[0])
        return VisionScore(margin=round(margin, 3), candidate=bool(margin > 0.0))

    def render_training_example(self, label: int, seed: int = 5) -> Image.Image:
        return _example_layout(label, seed)
