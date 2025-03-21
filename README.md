# API de Reconhecimento Facial

Esta API permite verificar faces em um vídeo contra uma base de fotos de referência.

## Requisitos

- Python 3.8 ou superior
- Bibliotecas listadas em `requirements.txt`

## Instalação

1. Crie um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # No Linux/Mac
# ou
.\venv\Scripts\activate  # No Windows
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Configuração

1. Crie uma pasta chamada `reference_photos` no mesmo diretório do script
2. Adicione as fotos de referência nesta pasta (formatos suportados: .jpg, .jpeg, .png)
3. O nome do arquivo da foto será usado como identificador

## Uso

1. Inicie o servidor:
```bash
python facial_recognition_api.py
```

2. A API estará disponível em `http://localhost:8000`

3. Endpoint disponível:
   - POST `/verify-face`: Recebe um arquivo de vídeo e verifica se há faces correspondentes

## Exemplo de uso com curl

```bash
curl -X POST -F "video=@caminho/do/seu/video.mp4" http://localhost:8000/verify-face
```

## Respostas

- Sucesso (200):
  ```json
  {
    "status": "ok",
    "message": "Face correspondente encontrada"
  }
  ```
  ou
  ```json
  {
    "status": "not_found",
    "message": "Nenhuma face correspondente encontrada"
  }
  ```

- Erro (400/500):
  ```json
  {
    "error": "Mensagem de erro"
  }
  ``` 