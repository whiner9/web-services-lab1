from flask import Flask, render_template, request, redirect, url_for
from flask_wtf import FlaskForm, RecaptchaField
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import RadioField, SubmitField
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import os
import uuid
import io
import base64

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- Настройка Google reCAPTCHA ---
app.config['RECAPTCHA_USE_SSL'] = False
app.config['RECAPTCHA_PUBLIC_KEY'] = '6LemcPwrAAAAAIYgs6n-eLG8IOHyflc85VDuT9Tz'
app.config['RECAPTCHA_PRIVATE_KEY'] = '6LemcPwrAAAAAPE2uXznN6l80ur37VyNkfGuajrD'

class ImageForm(FlaskForm):
    image1 = FileField(
        'Изображение 1',
        validators=[FileRequired(message="Выберите файл"), FileAllowed(['png', 'jpg', 'jpeg'], 'Только изображения!')],
        render_kw={"accept": "image/*"}
    )
    image2 = FileField(
        'Изображение 2',
        validators=[FileRequired(message="Выберите файл"), FileAllowed(['png', 'jpg', 'jpeg'], 'Только изображения!')],
        render_kw={"accept": "image/*"}
    )
    direction = RadioField(
        'Направление склейки',
        choices=[('horizontal', 'По горизонтали'), ('vertical', 'По вертикали')],
        default='horizontal'
    )
    recaptcha = RecaptchaField()
    submit = SubmitField('Обработать')

def create_color_histogram(image_array, filename):
    """Создаёт график распределения цветов RGB."""
    plt.figure(figsize=(12, 4))
    colors = ['red', 'green', 'blue']
    for i, color in enumerate(colors):
        plt.subplot(1, 3, i + 1)
        plt.hist(image_array[:, :, i].flatten(), bins=50, color=color, alpha=0.7)
        plt.title(f'{color.upper()} channel')
        plt.xlabel('Intensity')
        plt.ylabel('Frequency')
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    form = ImageForm()
    if form.validate_on_submit():
        file1 = form.image1.data
        file2 = form.image2.data
        direction = form.direction.data

        # Открываем изображения
        img1 = Image.open(file1).convert('RGB')
        img2 = Image.open(file2).convert('RGB')

        # Конвертируем в массивы
        arr1 = np.array(img1)
        arr2 = np.array(img2)

        # Создаём гистограммы (в памяти)
        hist1_base64 = create_histogram_base64(arr1)
        hist2_base64 = create_histogram_base64(arr2)

        # Изменяем размер второго изображения
        if direction == 'horizontal':
            new_height = img1.height
            img2 = img2.resize((img2.width, new_height), Image.Resampling.LANCZOS)
        else:
            new_width = img1.width
            img2 = img2.resize((new_width, img2.height), Image.Resampling.LANCZOS)

        arr2 = np.array(img2)

        # Склеиваем
        if direction == 'horizontal':
            combined_arr = np.concatenate((arr1, arr2), axis=1)
        else:
            combined_arr = np.concatenate((arr1, arr2), axis=0)

        # Конвертируем все изображения в base64
        img1_base64 = image_to_base64(img1)
        img2_base64 = image_to_base64(img2)
        combined_base64 = image_to_base64(Image.fromarray(combined_arr))
        hist_comb_base64 = create_histogram_base64(combined_arr)

        # Передаём в шаблон
        result_images = {
            'img1': img1_base64,
            'img2': img2_base64,
            'combined': combined_base64,
            'hist1': hist1_base64,
            'hist2': hist2_base64,
            'hist_comb': hist_comb_base64
        }

        return render_template('result.html', images=result_images)

    return render_template('index.html', form=form)

def image_to_base64(img):
    """Конвертирует PIL-изображение в base64 строку."""
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"

def create_histogram_base64(image_array):
    """Создаёт гистограмму и возвращает её как base64."""
    fig = plt.figure(figsize=(12, 4))
    colors = ['red', 'green', 'blue']
    for i, color in enumerate(colors):
        plt.subplot(1, 3, i + 1)
        plt.hist(image_array[:, :, i].flatten(), bins=50, color=color, alpha=0.7)
        plt.title(f'{color.upper()} channel')
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.getvalue()).decode()
    plt.close(fig)
    return f"data:image/png;base64,{img_base64}"

if __name__ == '__main__':
    app.run()