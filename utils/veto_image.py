import logging
import os
import pathlib
from logging.config import fileConfig

from PIL import Image, ImageDraw, ImageEnhance, ImageFont


class VetoImage:
    '''Represents a veto image

    Object used to create a veto image where the vetoed maps are crossed out
    with an x

    Attributes
    -----------
    map_images_fp: :class:`str`
        The file path of the CSGO map images preferably in ``.png`` format
        where the names of the images is the name of the map
    x_image_fp: :class:`str`
        The file path of the image containing an x which will be used when
        crossing out vetoed maps
    image_extension: :class:`str`
        The image extension of the image maps which will also be used when
        creating the result image
    assets_fp: :class:`str`
        The file path of a folder where the assets created will be stored
    font_fp: :class:`str`
        The file path of the font used when labeling the map icons
    logger: :object:`logger`
        The logger for the file
    '''

    def __init__(self, map_images_fp, x_image_fp, image_extension, assets_fp='veto_image_assets',
                 font_fp='fonts/Arialbd.TTF'):
        fileConfig('logging.conf')
        self.logger = logging.getLogger(f'10man.{__name__}')

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

    @staticmethod
    def resize(image, percentage, output_fp=None):
        '''Resizes the image based on the percentage provided

        The aspect ratio will be preserved

        Attributes
        -----------
        image: Union[:class:`str`, :class:`PIL.Image`]
            The filepath of the image or the image object itself
        percentage: :class:`float`
            The percentage size of the new image e.g 0.5 will reduce the size
            of the image by half
        output_fp: Optional[:class:`str`]
            If specified the image will be saved at the file path specified
        '''

        if isinstance(image, str):
            image = Image.open(image)

        image_width, image_height = image.size
        new_size = (image_width * percentage,
                    image_height * percentage)
        new_size = tuple(map(int, new_size))
        image = image.resize(new_size)

        if output_fp:
            image.save(output_fp)

        return image

    def __crop_map_images(self):
        '''Creates the map icon assets by cropping them and placing the
        cropped images into the assets folder
        '''

        self.logger.debug(f'__crop_map_images')

        for image_file_name in os.listdir(self.map_images_fp):
            image = Image.open(os.path.join(
                self.map_images_fp, image_file_name))
            image_width, image_height = image.size

            percentage = 0.25
            crop_coodinates = (0, image_height / 3, image_width,
                               image_height * 2 / 3)
            map_strip = image.crop(crop_coodinates)
            map_strip = VetoImage.resize(map_strip, percentage)

            map_strip.save(os.path.join(self.assets_fp, image_file_name))

    def __add_map_name(self):
        '''Adds the map names to each of the maps in the assets folder

        The image is also darkened to enhance clarity
        '''

        self.logger.debug(f'__add_map_name')

        font = None

        for image_file_name in os.listdir(self.assets_fp):
            image_root_name, _ = os.path.splitext(image_file_name)
            image_fp = os.path.join(self.assets_fp, image_file_name)
            image = Image.open(image_fp)
            image_width, image_height = image.size

            enhancer = ImageEnhance.Brightness(image)
            factor = 0.5
            darkened_image = enhancer.enhance(factor)

            if font is None:
                font = ImageFont.truetype(self.font_fp, int(image_width / 15))
            draw = ImageDraw.Draw(darkened_image)

            text_width, text_height = draw.textsize(image_root_name, font=font)
            draw.text(((image_width - text_width) / 2, (image_height - text_height) / 2),
                      text=image_root_name, font=font, align='center')

            darkened_image.save(image_fp)

    def __initialise_assets(self):
        '''Creates the assets by cropping the images and adding the map
        names
        '''

        self.logger.debug(f'__initialise_assets')

        assets = pathlib.Path(self.assets_fp)
        assets.mkdir(parents=True, exist_ok=True)

        self.__crop_map_images()
        self.__add_map_name()

    def construct_veto_image(self, map_list, output_fp, is_vetoed, spacing=0):
        ''' Outputs an image containing all the maps where all the vetoed
        maps are crossed out

        Parameters
        -----------
        map_list: :class:`list` of :class:`str`
            The list of maps to be included in the veto image
        output_fp: :class:`str`
            The filepath of the output veto image
        is_vetoed: :class:`list` of :class:`bool`
            The list of vetoed maps where the indices match up with the
            map_list parameter that is if is_vetoed[index] is True,
            map_list[index] is vetoed
        spacing: :class:`int`
            The spacing in pixels between the map icons
        '''

        self.logger.debug(f'construct_veto_image')

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
        num_rows = (len(map_list) + 1) // 2
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
        self.logger.info('Generated Updated Veto Image')
