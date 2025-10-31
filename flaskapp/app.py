from flask import Flask, render_template, request, redirect, url_for
from flask_wtf import FlaskForm, RecaptchaField
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import RadioField, SubmitField
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import os
import uuid

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

        # Генерируем уникальный ID
        unique_id = str(uuid.uuid4())

        # Пути к файлам
        path1 = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_1.png")
        path2 = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_2.png")
        path_combined = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_combined.png")
        path_hist1 = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_hist1.png")
        path_hist2 = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_hist2.png")
        path_hist_comb = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_hist_comb.png")

        # Открываем изображения
        img1 = Image.open(file1).convert('RGB')
        img2 = Image.open(file2).convert('RGB')

        # Конвертируем в массивы NumPy
        arr1 = np.array(img1)
        arr2 = np.array(img2)

        # Сохраняем исходные изображения
        img1.save(path1)
        img2.save(path2)

        # Создаём гистограммы
        create_color_histogram(arr1, path_hist1)
        create_color_histogram(arr2, path_hist2)

        # Склеиваем
        if direction == 'horizontal':
            # Убедимся, что высоты одинаковы
            if img1.height != img2.height:
                new_width = int(img2.width * img1.height / img2.height)
                img2 = img2.resize((new_width, img1.height), Image.Resampling.LANCZOS)
                arr2 = np.array(img2)
            combined_arr = np.concatenate((arr1, arr2), axis=1)
        else:  # vertical
            # Убедимся, что ширины одинаковы
            if img1.width != img2.width:
                new_height = int(img2.height * img1.width / img2.width)
                img2 = img2.resize((img1.width, new_height), Image.Resampling.LANCZOS)
                arr2 = np.array(img2)
            combined_arr = np.concatenate((arr1, arr2), axis=0)

        # Сохраняем результат
        combined_img = Image.fromarray(combined_arr)
        combined_img.save(path_combined)
        create_color_histogram(combined_arr, path_hist_comb)

        # Формируем пути для шаблона
        result_images = {
            'img1': f'uploads/{unique_id}_1.png',
            'img2': f'uploads/{unique_id}_2.png',
            'combined': f'uploads/{unique_id}_combined.png',
            'hist1': f'uploads/{unique_id}_hist1.png',
            'hist2': f'uploads/{unique_id}_hist2.png',
            'hist_comb': f'uploads/{unique_id}_hist_comb.png'
        }

        return render_template('result.html', images=result_images)

    return render_template('index.html', form=form)

if __name__ == '__main__':
    app.run()