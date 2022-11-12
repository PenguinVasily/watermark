from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.exceptions import HTTPException
from PIL import Image
import io


from settings import *


def image_to_bytes(image: Image, image_format='PNG') -> bytes:
    result = io.BytesIO()
    image.save(result, format=image_format)
    return result.getvalue()


def paste_watermark(image: bytes, mode: str) -> bytes:
    watermark = Image.open(WATERMARK_PATH).convert('RGBA')
    editable_image = Image.open(io.BytesIO(image)).convert('RGBA')



    if mode == 'FILL':
        watermark.thumbnail((editable_image.width / 100 * FILL_WATERMARK_RESIZE_PERCENT,
                             editable_image.height / 100 * FILL_WATERMARK_RESIZE_PERCENT))

        horizontal_indent = int(watermark.width / 100 * HORIZONTAL_INDENT_PERCENT)
        vertical_indent = int(watermark.height / 100 * VERTICAL_INDENT_PERCENT)

        for i in range(0, int(editable_image.width / (watermark.width + horizontal_indent)) + 1):
            for j in range(0, int(editable_image.height / (watermark.height + vertical_indent)) + 1):
                x, y = (watermark.width + horizontal_indent) * i, (watermark.height + vertical_indent) * j
                editable_image.alpha_composite(watermark, (x, y))

    elif mode == 'CENTER':
        watermark.thumbnail((editable_image.width / 100 * CENTER_WATERMARK_RESIZE_PERCENT,
                             editable_image.height / 100 * CENTER_WATERMARK_RESIZE_PERCENT))

        background_center_x, background_center_y = int(editable_image.width / 2), int(editable_image.height / 2)
        watermark_center_x, watermark_center_y = int(watermark.width / 2), int(watermark.height / 2)
        editable_image.alpha_composite(watermark, (background_center_x - watermark_center_x,
                                                   background_center_y - watermark_center_y))
    else:
        raise HTTPException(status_code=404, detail="Неизвестный режим заполнения")
    return image_to_bytes(editable_image)


app = FastAPI()


@app.post("/{mode}")
async def put_watermark(mode: str, image: UploadFile):
    return StreamingResponse(io.BytesIO(paste_watermark(image.file.read(), mode.upper())), media_type=image.content_type)
