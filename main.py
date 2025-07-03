import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton,
                             QLabel, QFileDialog, QLineEdit, QHBoxLayout, QMessageBox, QComboBox)
from PyQt5.QtGui import QPixmap, QImage, QIntValidator
from PyQt5.QtCore import Qt


class ImageProcessorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Обработка изображений")
        self.setGeometry(100, 100, 800, 700)

        self.image = None  # Текущее изображение, с которым работаем
        self.original_image = None  # Оригинальное изображение после загрузки или захвата с камеры

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        #Загрузка изображения / захват с веб-камеры
        input_layout = QHBoxLayout()
        self.load_button = QPushButton("Загрузить изображение")
        self.load_button.clicked.connect(self.load_image)
        input_layout.addWidget(self.load_button)

        self.webcam_button = QPushButton("Сделать фото с веб-камеры")
        self.webcam_button.clicked.connect(self.capture_from_webcam)
        input_layout.addWidget(self.webcam_button)
        main_layout.addLayout(input_layout)

        #Отображение изображения
        self.image_label = QLabel("Здесь будет ваше изображение")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(600, 400)
        self.image_label.setStyleSheet("border: 1px solid gray;")
        main_layout.addWidget(self.image_label)

        #Выбор канала
        channel_layout = QHBoxLayout()
        channel_label = QLabel("Показать канал:")
        channel_layout.addWidget(channel_label)
        self.channel_combo = QComboBox()
        self.channel_combo.addItems(["Все", "Красный", "Зеленый", "Синий"])
        self.channel_combo.currentIndexChanged.connect(self.show_channel)
        channel_layout.addWidget(self.channel_combo)
        channel_layout.addStretch()
        main_layout.addLayout(channel_layout)

        #Обрезка
        crop_group_layout = QVBoxLayout()
        crop_group_layout.addWidget(QLabel("Обрезка изображения"))
        crop_input_layout = QHBoxLayout()
        crop_label = QLabel("Координаты (x, y, w, h):")
        crop_input_layout.addWidget(crop_label)
        self.crop_x = QLineEdit("0")
        self.crop_y = QLineEdit("0")
        self.crop_w = QLineEdit("100")
        self.crop_h = QLineEdit("100")
        self.crop_x.setValidator(QIntValidator(0, 9999))
        self.crop_y.setValidator(QIntValidator(0, 9999))
        self.crop_w.setValidator(QIntValidator(1, 9999))
        self.crop_h.setValidator(QIntValidator(1, 9999))
        crop_input_layout.addWidget(self.crop_x)
        crop_input_layout.addWidget(self.crop_y)
        crop_input_layout.addWidget(self.crop_w)
        crop_input_layout.addWidget(self.crop_h)
        crop_button = QPushButton("Обрезать")
        crop_button.clicked.connect(self.crop_image)
        crop_input_layout.addWidget(crop_button)
        crop_group_layout.addLayout(crop_input_layout)
        main_layout.addLayout(crop_group_layout)

        #Вращение
        rotate_group_layout = QVBoxLayout()
        rotate_group_layout.addWidget(QLabel("Вращение изображения"))
        rotate_input_layout = QHBoxLayout()
        rotate_label = QLabel("Угол вращения (градусы):")
        rotate_input_layout.addWidget(rotate_label)
        self.rotate_angle = QLineEdit("0")
        self.rotate_angle.setValidator(QIntValidator(-360, 360))
        rotate_input_layout.addWidget(self.rotate_angle)
        rotate_button = QPushButton("Вращать")
        rotate_button.clicked.connect(self.rotate_image)
        rotate_input_layout.addWidget(rotate_button)
        rotate_group_layout.addLayout(rotate_input_layout)
        main_layout.addLayout(rotate_group_layout)

        #Рисование прямоугольника
        rect_group_layout = QVBoxLayout()
        rect_group_layout.addWidget(QLabel("Нарисовать прямоугольник (синий)"))
        rect_input_layout = QHBoxLayout()
        rect_label = QLabel("Координаты (x, y, w, h):")
        rect_input_layout.addWidget(rect_label)
        self.rect_x = QLineEdit("0")
        self.rect_y = QLineEdit("0")
        self.rect_w = QLineEdit("50")
        self.rect_h = QLineEdit("50")
        self.rect_x.setValidator(QIntValidator(0, 9999))
        self.rect_y.setValidator(QIntValidator(0, 9999))
        self.rect_w.setValidator(QIntValidator(1, 9999))
        self.rect_h.setValidator(QIntValidator(1, 9999))
        rect_input_layout.addWidget(self.rect_x)
        rect_input_layout.addWidget(self.rect_y)
        rect_input_layout.addWidget(self.rect_w)
        rect_input_layout.addWidget(self.rect_h)
        rect_button = QPushButton("Нарисовать прямоугольник")
        rect_button.clicked.connect(self.draw_rectangle)
        rect_input_layout.addWidget(rect_button)
        rect_group_layout.addLayout(rect_input_layout)
        main_layout.addLayout(rect_group_layout)

        #Сброс изображения
        reset_button = QPushButton("Сбросить изображение")
        reset_button.clicked.connect(self.reset_image)
        main_layout.addWidget(reset_button)

        main_layout.addStretch()  # Для выравнивания элементов сверху

        self.setLayout(main_layout)

    def display_image(self, img):
        if img is None:
            self.image_label.setText("Нет изображения для отображения.")
            self.image = None
            return

        if not img.flags['C_CONTIGUOUS']:
            img = np.ascontiguousarray(img)

        if img.dtype != np.uint8:
            img = img.astype(np.uint8)

        if len(img.shape) == 3:  # Цветное изображение (BGR)
            h, w, ch = img.shape
            bytes_per_line = ch * w
            convert_to_Qt_format = QImage(img.data, w, h, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        elif len(img.shape) == 2:  # Черно-белое изображение
            h, w = img.shape
            bytes_per_line = w
            convert_to_Qt_format = QImage(img.data, w, h, bytes_per_line, QImage.Format_Grayscale8)
        else:  # На всякий случай, если формат изображения неожиданный
            QMessageBox.critical(self, "Ошибка отображения",
                                 "Неподдерживаемый формат изображения для отображения (ожидается 2 или 3 канала).")
            self.image_label.setText("Ошибка: Неподдерживаемый формат.")
            return

        # Масштабируем изображение для отображения в QLabel, сохраняя пропорции
        p = convert_to_Qt_format.scaled(self.image_label.width(), self.image_label.height(), Qt.KeepAspectRatio,
                                        Qt.SmoothTransformation)
        self.image_label.setPixmap(QPixmap.fromImage(p))
        self.image = img

    def load_image(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Выбрать изображение", "",
                                                   "Images (*.png *.jpg);;All Files (*)", options=options)
        if file_name:
            try:
                img = cv2.imread(file_name)
                if img is None:
                    raise IOError(
                        "Не удалось загрузить изображение. Возможно, файл поврежден, не существует или имеет неподдерживаемый формат.")

                self.original_image = img.copy()  # Сохраняем оригинал для сброса
                self.display_image(img)  # Отображаем загруженное изображение
                QMessageBox.information(self, "Успех", "Изображение успешно загружено!")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка загрузки", f"Произошла ошибка при загрузке изображения: {e}")
                self.image_label.setText("Ошибка загрузки изображения.")
                self.image = None  # Сбросить текущее изображение

    def capture_from_webcam(self):
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            QMessageBox.critical(self, "Ошибка веб-камеры",
                                 "Не удалось подключиться к веб-камере. Возможные причины и решения:\n"
                                 "1. Веб-камера занята другим приложением.\n"
                                 "2. Отсутствуют драйверы или они устарели.\n"
                                 "3. Нет разрешений на доступ к веб-камере для данного приложения.\n"
                                 "4. Веб-камера отключена или не подключена."
                                 "\nПопробуйте перезагрузить компьютер, проверить настройки конфиденциальности или обновить драйверы.")
            cap.release()
            return

        ret, frame = cap.read()
        cap.release()

        if ret:
            self.original_image = frame.copy()  # Сохраняем оригинал
            self.display_image(frame)
            QMessageBox.information(self, "Успех", "Фото снимок сделан!")
        else:
            QMessageBox.warning(self, "Ошибка веб-камеры",
                                "Не удалось сделать фото снимок. Возможно, камера неактивна или возникла другая проблема.")
            self.image_label.setText("Ошибка захвата с камеры.")
            self.image = None  # Сбросить текущее изображение

    def show_channel(self):
        if self.original_image is None:
            QMessageBox.warning(self, "Ошибка", "Сначала загрузите изображение.")
            return

        channel_index = self.channel_combo.currentIndex()
        current_img_copy = self.original_image.copy()  # Копируем оригинал, чтобы не изменять его

        if len(current_img_copy.shape) < 3:  # Если изображение черно-белое, каналы не применимы
            QMessageBox.warning(self, "Информация", "Изображение черно-белое. Каналы не применимы.")
            self.display_image(self.original_image)
            self.channel_combo.setCurrentIndex(0)
            return

        if channel_index == 0:  # Все каналы
            self.display_image(current_img_copy)
            QMessageBox.information(self, "Отклик", "Отображены все каналы.")
        else:
            b, g, r = cv2.split(current_img_copy)
            zeros = np.zeros_like(b)  # Массив нулей такого же размера

            if channel_index == 1:  # Красный канал
                red_channel_img = cv2.merge([zeros, zeros, r])
                self.display_image(red_channel_img)
                QMessageBox.information(self, "Отклик", "Отображен красный канал.")
            elif channel_index == 2:  # Зеленый канал
                green_channel_img = cv2.merge([zeros, g, zeros])
                self.display_image(green_channel_img)
                QMessageBox.information(self, "Отклик", "Отображен зеленый канал.")
            elif channel_index == 3:  # Синий канал
                blue_channel_img = cv2.merge([b, zeros, zeros])
                self.display_image(blue_channel_img)
                QMessageBox.information(self, "Отклик", "Отображен синий канал.")

    def crop_image(self):
        if self.image is None:
            QMessageBox.warning(self, "Ошибка", "Сначала загрузите изображение.")
            return

        try:
            # Получаем текущие размеры изображения для валидации
            img_h, img_w = self.image.shape[:2]

            x = int(self.crop_x.text())
            y = int(self.crop_y.text())
            w = int(self.crop_w.text())
            h = int(self.crop_h.text())

            # Валидация входных координат и размеров
            if not (0 <= x < img_w and 0 <= y < img_h and
                    w > 0 and h > 0 and
                    x + w <= img_w and y + h <= img_h):
                raise ValueError(f"Некорректные координаты или размеры для обрезки. "
                                 f"Размеры изображения: {img_w}x{img_h}. Заданы: x={x}, y={y}, w={w}, h={h}. "
                                 f"Убедитесь, что область обрезки находится внутри изображения.")

            cropped_img = self.image[y: y + h, x: x + w]
            self.display_image(cropped_img)  # Отображаем обрезанное изображение
            QMessageBox.information(self, "Отклик", f"Изображение обрезано по ({x},{y}) с размерами ({w},{h}).")
            self.channel_combo.setCurrentIndex(0)
        except ValueError as e:
            QMessageBox.critical(self, "Ошибка обрезки", f"Некорректный ввод: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка обрезки", f"Произошла непредвиденная ошибка при обрезке: {e}")

    def rotate_image(self):
        if self.image is None:
            QMessageBox.warning(self, "Ошибка", "Сначала загрузите изображение.")
            return

        try:
            angle = int(self.rotate_angle.text())
            (h, w) = self.image.shape[:2]
            center = (w // 2, h // 2)

            # Получаем матрицу поворота
            M = cv2.getRotationMatrix2D(center, angle, 1.0)

            # Применяем поворот, сохраняя исходные размеры
            rotated_img = cv2.warpAffine(self.image, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))

            self.display_image(rotated_img)
            QMessageBox.information(self, "Отклик", f"Изображение повернуто на {angle} градусов.")
            self.channel_combo.setCurrentIndex(0)
        except ValueError:
            QMessageBox.critical(self, "Ошибка вращения", "Некорректный ввод угла. Введите целое число.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка вращения", f"Произошла непредвиденная ошибка при вращении: {e}")

    def draw_rectangle(self):
        if self.image is None:
            QMessageBox.warning(self, "Ошибка", "Сначала загрузите изображение.")
            return

        try:
            # Получаем текущие размеры изображения для валидации
            img_h, img_w = self.image.shape[:2]

            x = int(self.rect_x.text())
            y = int(self.rect_y.text())
            w = int(self.rect_w.text())
            h = int(self.rect_h.text())

            # Валидация входных координат и размеров для прямоугольника
            if not (0 <= x < img_w and 0 <= y < img_h and w > 0 and h > 0):
                raise ValueError(f"Некорректные координаты или размеры для прямоугольника. "
                                 f"Размеры изображения: {img_w}x{img_h}. Заданы: x={x}, y={y}, w={w}, h={h}. "
                                 f"Начальная точка должна быть внутри изображения, а ширина/высота положительными.")

            img_with_rect = self.image.copy()
            # Рисуем синий прямоугольник, толщина 2 пикселя
            cv2.rectangle(img_with_rect, (x, y), (x + w, y + h), (255, 0, 0), 2)

            self.display_image(img_with_rect)
            QMessageBox.information(self, "Отклик",
                                    f"Нарисован синий прямоугольник по ({x},{y}) с размерами ({w},{h}).")
            self.channel_combo.setCurrentIndex(0)
        except ValueError as e:
            QMessageBox.critical(self, "Ошибка рисования", f"Некорректный ввод: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка рисования", f"Произошла непредвиденная ошибка при рисовании: {e}")

    def reset_image(self):
        if self.original_image is not None:
            self.display_image(self.original_image.copy())  # Отображаем копию оригинала
            self.channel_combo.setCurrentIndex(0)  # Сброс выбора канала на "Все"
            QMessageBox.information(self, "Отклик", "Изображение сброшено до оригинала.")
        else:
            QMessageBox.warning(self, "Ошибка",
                                "Нет оригинального изображения для сброса. Сначала загрузите изображение.")
            self.image_label.setText("Нет изображения.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = ImageProcessorApp()
    ex.show()
    sys.exit(app.exec_())