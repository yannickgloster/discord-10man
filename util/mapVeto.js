const fs = require("fs");
const path = require("path");
const sharp = require("sharp");

let instance = null;

class MapVetoImageFactory {
  constructor(mapImagesFilePath, assetsFilePath) {
    if (!instance) {
      instance = this;
    }

    this.mapImagesFilePath = mapImagesFilePath;
    this.assetsFilePath = assetsFilePath;

    return instance;
  }

  static getTextOverlay(text, width, height, x, y) {
    const textOverlay = `
      <svg width="${width}" height="${height}">
        <style>
          text {
            font-family: sans-serif;
            text-anchor: middle;
            fill: white;
            font-size: 3em;
            font-weight: bold;
          }
        </style>
        <text x="${x}" y="${y}">${text}</text>
      </svg>
    `;
    return textOverlay;
  }

  static async addImageNumber(image, imageNumber) {
    const metadata = await image.metadata();
    const textOverlay = MapVetoImageFactory.getTextOverlay(
      imageNumber,
      metadata.width,
      metadata.height,
      "5%",
      "55%"
    );

    return image.composite([{ input: Buffer.from(textOverlay) }]).toBuffer();
  }

  static async addMapName(image, mapName) {
    const metadata = await image.metadata();
    const textOverlay = MapVetoImageFactory.getTextOverlay(
      mapName,
      metadata.width,
      metadata.height,
      "50%",
      "55%"
    );

    return image.composite([{ input: Buffer.from(textOverlay) }]).toBuffer();
  }

  static async cropImage(image) {
    const metadata = await image.metadata();
    return image
      .extract({
        left: 0,
        top: metadata.height / 3,
        width: metadata.width,
        height: (metadata.height * 2) / 3,
      })
      .toBuffer();
  }

  static async resizeImage(image, percentage) {
    const metadata = await image.metadata();
    return image
      .resize(metadata.width * percentage, metadata.height * percentage)
      .toBuffer();
  }

  async initialiseAssets() {
    const assetsFilePath = this.assetsFilePath;
    try {
      await fs.promises.mkdir(assetsFilePath);
    } catch (err) {
      if (err.code !== "EEXIST") {
        throw err;
      }
    }

    const mapFileNames = await fs.promises.readdir(this.mapImagesFilePath);
    await Promise.all(
      mapFileNames.map(async (mapFileName) => {
        const mapName = path.parse(mapFileName).name;
        const mapFilePath = path.join(this.mapImagesFilePath, mapFileName);
        const mapOutputFilePath = path.join(this.assetsFilePath, mapFileName);

        // Crop image
        const mapImage = sharp(mapFilePath);
        const croppedImageBuffer = await MapVetoImageFactory.cropImage(
          mapImage
        );

        // Resize image
        const croppedImage = sharp(croppedImageBuffer);
        const resizedImageBuffer = await MapVetoImageFactory.resizeImage(
          croppedImage,
          0.25
        );

        // Add map name
        const resizedImage = sharp(resizedImageBuffer)
          .gamma(2.2, 1.5)
          .blur(1.5);
        const mapImageWithNameBuffer = await MapVetoImageFactory.addMapName(
          resizedImage,
          mapName
        );

        // Save image
        await sharp(mapImageWithNameBuffer)
          .withMetadata()
          .png()
          .toFile(mapOutputFilePath);
      })
    );
  }
}

Object.freeze(MapVetoImageFactory);

module.exports = MapVetoImageFactory;
