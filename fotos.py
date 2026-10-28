from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError


def converter_para_jpeg(arquivo, tamanho_maximo=(400, 400)):
    """
    Converte uma imagem para JPEG, limita suas dimensões
    e retorna os bytes prontos para armazenamento no SQLite.

    Aceita um arquivo enviado pelo Streamlit ou bytes.
    """
    try:
        with Image.open(
            BytesIO(arquivo.read() if hasattr(arquivo, "read") else arquivo)
        ) as imagem:
            # Corrige a orientação de fotografias de celulares.
            imagem = ImageOps.exif_transpose(imagem)

            # JPEG não suporta transparência.
            if imagem.mode in ("RGBA", "LA") or (
                imagem.mode == "P" and "transparency" in imagem.info
            ):
                rgba = imagem.convert("RGBA")
                fundo = Image.new("RGB", rgba.size, "white")
                fundo.paste(rgba, mask=rgba.getchannel("A"))
                imagem = fundo
            else:
                imagem = imagem.convert("RGB")

            # Redimensiona sem distorcer e sem ampliar.
            imagem.thumbnail(tamanho_maximo, Image.Resampling.LANCZOS)

            saida = BytesIO()
            imagem.save(saida, format="JPEG", quality=75, optimize=True)

            return saida.getvalue()

    except (UnidentifiedImageError, OSError, ValueError) as erro:
        raise ValueError(
            "O arquivo enviado não é uma imagem válida ou suportada."
        ) from erro
