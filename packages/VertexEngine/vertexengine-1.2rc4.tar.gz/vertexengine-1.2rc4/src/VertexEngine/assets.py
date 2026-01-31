import pygame
from PyQt6.QtGui import QImage
import typing_extensions as typing

@typing.deprecated('This is not a public API, use AssetManager pls :D')
class QtRenderer:
    def create_texture(self, image_asset):
        surf = image_asset.surface
        width, height = surf.get_size()

        # Ensure predictable format
        surf = surf.convert_alpha() if surf.get_alpha() else surf.convert()

        # pygame → raw RGBA
        pixel_data = pygame.image.tostring(surf, "RGBA", False)

        # Create REAL QImage (no OpenGL required)
        qimage = QImage(
            pixel_data,
            width,
            height,
            QImage.Format.Format_RGBA8888
        )

        # IMPORTANT: deep copy so data survives after function returns
        qimage = qimage.copy()

        return Texture(qimage)

@typing.deprecated('This is not a public API, use AssetManager pls :D')
class Texture:
    def __init__(self, qimage: QImage):
        self.image = qimage
        self.width = qimage.width()
        self.height = qimage.height()

    def __repr__(self):
        return f"<Texture {self.width}x{self.height} (QImage)>"

@typing.deprecated('This is not a public API, use AssetManager pls :D')
class ImageAsset:
    def __init__(self, surface):
        self.surface = surface  # pygame.Surface

class AssetManager:
    def __init__(self):
        self.images = {}

    def load_image(self, name: str, path: str):
        if name in self.images:
            return self.images[name]

        try:
            surface = pygame.image.load(path).convert_alpha()
            self.images[name] = surface
            return surface

        except FileNotFoundError:
            print(f"[Warning] Image '{path}' not found!")
            return None

    def get_image(self, name: str):
        return self.images.get(name)
