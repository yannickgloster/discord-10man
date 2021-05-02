const fs = require("fs");
const path = require("path");
const sharp = require("sharp");

let instance = null;

class MapVetoImageFactory {
  constructor(mapImagesFilePath, crossMarkFilePath, assetsFilePath) {
    if (!instance) {
      instance = this;
    }

    this.mapImagesFilePath = mapImagesFilePath;
    this.crossMarkFilePath = crossMarkFilePath;
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

  static async addCrossMark(image, crossMarkImage, size) {
    const input = await crossMarkImage.resize(size).toBuffer();

    return image.composite([{ input }]).toBuffer();
  }

  async initialiseAssets() {
    try {
      await fs.promises.mkdir(this.assetsFilePath);
    } catch (err) {
      if (err.code !== "EEXIST") {
        throw err;
      }
    }

    const mapFileNames = await fs.promises.readdir(this.mapImagesFilePath);
    await Promise.all(
      mapFileNames.map(async (mapFileName) => {
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

        // Save image
        await sharp(resizedImageBuffer)
          .withMetadata()
          .png()
          .toFile(mapOutputFilePath);
      })
    );
  }

  async createMapVetoImage(mapsVetoed, spacing = 20) {
    const placeholderImageFilePath = path.join(
      this.assetsFilePath,
      "de_placeholder.png"
    );
    const placeholderImage = sharp(placeholderImageFilePath);
    const placeholderImageMetadata = await placeholderImage.metadata();

    const mapNames = Object.keys(mapsVetoed);

    const numRows = Math.floor((mapNames.length + 1) / 2);
    const width = placeholderImageMetadata.width * 2 + spacing;
    const height =
      placeholderImageMetadata.height * numRows + spacing * (numRows - 1);

    const mapVetoImage = sharp({
      create: {
        width,
        height,
        channels: 4,
        //transparent background
        background: { r: 0, g: 0, b: 0, alpha: 0 },
      },
    });

    const assetsFilePaths = (
      await fs.promises.readdir(this.assetsFilePath)
    ).map((fileName) => path.join(this.assetsFilePath, fileName));
    const overlayOptionPromises = [];
    let mapIndex = 0;

    for (
      let top = 0;
      top < height;
      top += placeholderImageMetadata.height + spacing
    ) {
      for (
        let left = 0;
        left < width;
        left += placeholderImageMetadata.width + spacing, mapIndex += 1
      ) {
        if (mapIndex == mapNames.length) {
          break;
        }

        const currentMapName = mapNames[mapIndex];
        const [assetFilePath] = assetsFilePaths.filter((filePath) =>
          filePath.includes(currentMapName)
        );

        const currentMapImage = sharp(
          assetFilePath ? assetFilePath : placeholderImageFilePath
        );

        overlayOptionPromises.push(
          (async () => {
            const imageNumber = mapIndex + 1;
            const currentMapVetoed = mapsVetoed[currentMapName];
            // Darken image
            currentMapImage.gamma(2.2, 1.5).blur(1.5);
            // Add map name
            const mapImageWithNameBuffer = await MapVetoImageFactory.addMapName(
              currentMapImage,
              currentMapName
            );

            // Add map index
            const mapImageWithIndexNumberBuffer = await MapVetoImageFactory.addImageNumber(
              sharp(mapImageWithNameBuffer),
              imageNumber
            );

            // Add cross mark if vetoed
            const input = !currentMapVetoed
              ? mapImageWithIndexNumberBuffer
              : await MapVetoImageFactory.addCrossMark(
                  sharp(mapImageWithIndexNumberBuffer),
                  sharp(this.crossMarkFilePath),
                  placeholderImageMetadata.height / 2
                );

            return { input, top, left };
          })()
        );
      }
    }

    const overlayOptions = await Promise.all(overlayOptionPromises);

    return mapVetoImage
      .composite(overlayOptions)
      .withMetadata()
      .png()
      .toBuffer();
  }
}

Object.freeze(MapVetoImageFactory);

module.exports = MapVetoImageFactory;
