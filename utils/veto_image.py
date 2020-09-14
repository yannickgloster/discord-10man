from PIL import Image, ImageDraw, ImageEnhance, ImageFont
import pathlib
import os


class VetoImage:
    def __init__(self, map_images_fp, x_image_fp, image_extension, assets_fp='veto_image_assets', font_fp='fonts/Arialbd.TTF'):
        self.map_images_fp = map_images_fp
        self.image_extension = image_extension
        self.x_image_fp = x_image_fp
        self.assets_fp = assets_fp
        self.font_fp = font_fp
        self.__initialise_assets()

    @property
    def x_image_fp(self):
        return self._x_image_fp + self.image_extension

    @x_image_fp.setter
    def x_image_fp(self, value):
        if value.endswith(self.image_extension):
            x_image_root_name, _ = os.path.splitext(value)
            self._x_image_fp = x_image_root_name
        else:
            self._x_image_fp = value

    @property
    def image_extension(self):
        return self._image_extension

    @image_extension.setter
    def image_extension(self, value):
        if not value.startswith('.'):
            self._image_extension = '.' + value
        else:
            self._image_extension = value

    def __crop_map_images(self):
        for image_file_name in os.listdir(self.map_images_fp):
            image = Image.open(os.path.join(
                self.map_images_fp, image_file_name))
            image_width, image_height = image.size

            crop_coodinates = (0, image_height / 3, image_width,
                               image_height * 2 / 3)
            map_strip = image.crop(crop_coodinates)

            percentage = 0.25
            image_width, image_height = map_strip.size
            new_size = (int(image_width * percentage),
                        int(image_height * percentage))
            map_strip = map_strip.resize(new_size)

            map_strip.save(os.path.join(self.assets_fp, image_file_name))

    def __add_map_name(self):
        for image_file_name in os.listdir(self.assets_fp):
            image_root_name, _ = os.path.splitext(image_file_name)
            image_fp = os.path.join(self.assets_fp, image_file_name)
            image = Image.open(image_fp)
            image_width, image_height = image.size

            enhancer = ImageEnhance.Brightness(image)
            factor = 0.5
            darkened_image = enhancer.enhance(factor)

            font = ImageFont.truetype(self.font_fp, int(image_width / 15))
            draw = ImageDraw.Draw(darkened_image)

            text_width, text_height = draw.textsize(image_root_name, font=font)
            draw.text(((image_width - text_width) / 2, (image_height - text_height) / 2),
                      text=image_root_name, font=font, align='center')

            darkened_image.save(image_fp)

    def __initialise_assets(self):
        assets = pathlib.Path(self.assets_fp)
        assets.mkdir(parents=True, exist_ok=True)

        self.__crop_map_images()
        self.__add_map_name()

    def construct_veto_image(self, map_list, output_fp, is_vetoed=list(), spacing=0):
        if not output_fp.endswith(self.image_extension):
            output_fp = output_fp + self.image_extension

        first_image = Image.open(os.path.join(
            self.assets_fp, map_list[0] + self.image_extension))
        (first_image_width, first_image_height) = first_image.size

        x_image = Image.open(self.x_image_fp).convert('RGBA')
        x_image_new_size = (first_image_height / 2, first_image_height / 2)
        x_image_new_size = tuple(map(int, x_image_new_size))
        x_image = x_image.resize(x_image_new_size)
        (x_image_width, x_image_height) = x_image.size

        transparent_colour = (255, 0, 0, 0)
        num_rows = round(len(map_list) / 2)
        canvas_size = (first_image_width * 2 + spacing,
                       first_image_height * num_rows + spacing * (num_rows - 1))
        canvas = Image.new('RGBA', canvas_size, transparent_colour)
        font = ImageFont.truetype(self.font_fp, int(first_image_width / 15))

        index = 0
        for y in range(0, canvas_size[1], first_image_height + spacing):
            for x in range(0, canvas_size[0], first_image_width + spacing):
                if index == len(map_list):
                    break
                current_image = Image.open(os.path.join(
                    self.assets_fp, map_list[index] + self.image_extension))
                image_coords = (x, y)
                image_coords = tuple(map(int, image_coords))
                canvas.paste(current_image, image_coords)

                draw = ImageDraw.Draw(canvas)
                index_string = str(index + 1)
                text_width, text_height = draw.textsize(
                    index_string, font=font)
                draw.text((text_width + x, (first_image_height - text_height) / 2 + y),
                          text=index_string, font=font, align='center')

                if index < len(is_vetoed) and is_vetoed[index]:
                    x_image_coords = ((first_image_width - x_image_width) / 2 + x,
                                      (first_image_height - x_image_height) / 2 + y)
                    x_image_coords = tuple(map(int, x_image_coords))
                    canvas.paste(x_image, x_image_coords, mask=x_image)

                index += 1

        canvas.save(output_fp)
