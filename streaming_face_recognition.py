import cv2
import face_recognition
import numpy as np
from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse
import os
from typing import List
import asyncio
import json

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

@app.websocket("/ws/face-recognition")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Carrega as fotos de referência
    reference_encodings, reference_names = load_reference_photos()
    
    if not reference_encodings:
        await websocket.send_json({
            "error": "Nenhuma foto de referência encontrada"
        })
        return
    
    try:
        while True:
            # Recebe o frame do cliente
            data = await websocket.receive_bytes()
            
            # Converte os bytes recebidos em um frame numpy
            nparr = np.frombuffer(data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Converte o frame para RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Encontra faces no frame
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            
            # Lista para armazenar os resultados do frame atual
            frame_results = []
            
            # Verifica cada face encontrada
            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(reference_encodings, face_encoding)
                if True in matches:
                    matched_index = matches.index(True)
                    frame_results.append({
                        "status": "match",
                        "name": reference_names[matched_index]
                    })
                else:
                    frame_results.append({
                        "status": "no_match",
                        "name": "unknown"
                    })
            
            # Envia os resultados de volta para o cliente
            await websocket.send_json({
                "frame_results": frame_results,
                "faces_found": len(face_locations)
            })
            
    except Exception as e:
        await websocket.send_json({
            "error": str(e)
        })
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 