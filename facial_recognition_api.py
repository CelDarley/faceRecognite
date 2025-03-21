import cv2
import face_recognition
import numpy as np
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import os
from typing import List
import tempfile

app = FastAPI()

# Configuração do diretório de fotos de referência
REFERENCE_PHOTOS_DIR = "reference_photos"

def load_reference_photos():
    """Carrega as fotos de referência e seus encodings"""
    reference_encodings = []
    reference_names = []
    
    if not os.path.exists(REFERENCE_PHOTOS_DIR):
        os.makedirs(REFERENCE_PHOTOS_DIR)
        return reference_encodings, reference_names
    
    for filename in os.listdir(REFERENCE_PHOTOS_DIR):
        if filename.endswith((".jpg", ".jpeg", ".png")):
            path = os.path.join(REFERENCE_PHOTOS_DIR, filename)
            image = face_recognition.load_image_file(path)
            face_encodings = face_recognition.face_encodings(image)
            
            if face_encodings:
                reference_encodings.append(face_encodings[0])
                reference_names.append(os.path.splitext(filename)[0])
    
    return reference_encodings, reference_names

@app.post("/verify-face")
async def verify_face(video: UploadFile = File(...)):
    try:
        # Carrega as fotos de referência
        reference_encodings, reference_names = load_reference_photos()
        
        if not reference_encodings:
            return JSONResponse(
                content={"error": "Nenhuma foto de referência encontrada"},
                status_code=400
            )
        
        # Salva o vídeo temporariamente
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
            content = await video.read()
            temp_video.write(content)
            temp_video_path = temp_video.name
        
        # Abre o vídeo
        cap = cv2.VideoCapture(temp_video_path)
        
        # Processa alguns frames do vídeo
        frames_processed = 0
        max_frames = 30  # Limita o número de frames processados
        
        while frames_processed < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Converte o frame para RGB (necessário para face_recognition)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Encontra faces no frame
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            
            # Verifica cada face encontrada
            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(reference_encodings, face_encoding)
                if True in matches:
                    # Remove o arquivo temporário
                    os.unlink(temp_video_path)
                    return JSONResponse(
                        content={"status": "ok", "message": "Face correspondente encontrada"},
                        status_code=200
                    )
            
            frames_processed += 1
        
        # Limpa recursos
        cap.release()
        os.unlink(temp_video_path)
        
        return JSONResponse(
            content={"status": "not_found", "message": "Nenhuma face correspondente encontrada"},
            status_code=200
        )
        
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 