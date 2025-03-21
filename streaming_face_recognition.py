import cv2
import face_recognition
import numpy as np
from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from typing import List
import asyncio
import json
import logging

# Configuração de logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configuração do CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas as origens em desenvolvimento
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuração do diretório de fotos de referência
REFERENCE_PHOTOS_DIR = "reference_photos"

def load_reference_photos():
    """Carrega as fotos de referência e seus encodings"""
    reference_encodings = []
    reference_names = []
    
    if not os.path.exists(REFERENCE_PHOTOS_DIR):
        logger.warning(f"Diretório {REFERENCE_PHOTOS_DIR} não encontrado. Criando...")
        os.makedirs(REFERENCE_PHOTOS_DIR)
        return reference_encodings, reference_names
    
    files = os.listdir(REFERENCE_PHOTOS_DIR)
    logger.info(f"Encontrados {len(files)} arquivos no diretório de referência")
    
    for filename in files:
        if filename.endswith((".jpg", ".jpeg", ".png")):
            path = os.path.join(REFERENCE_PHOTOS_DIR, filename)
            logger.info(f"Processando arquivo: {filename}")
            
            try:
                image = face_recognition.load_image_file(path)
                face_encodings = face_recognition.face_encodings(image)
                
                if face_encodings:
                    logger.info(f"Face encontrada em {filename}")
                    reference_encodings.append(face_encodings[0])
                    reference_names.append(os.path.splitext(filename)[0])
                else:
                    logger.warning(f"Nenhuma face encontrada em {filename}")
            except Exception as e:
                logger.error(f"Erro ao processar {filename}: {str(e)}")
    
    logger.info(f"Total de faces de referência carregadas: {len(reference_encodings)}")
    return reference_encodings, reference_names

@app.websocket("/ws/face-recognition")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("Nova conexão WebSocket estabelecida")
    
    # Carrega as fotos de referência
    reference_encodings, reference_names = load_reference_photos()
    
    if not reference_encodings:
        logger.warning("Nenhuma foto de referência encontrada")
        await websocket.send_json({
            "error": "Nenhuma foto de referência encontrada"
        })
        return
    
    try:
        frame_count = 0
        while True:
            try:
                # Recebe o frame do cliente
                data = await websocket.receive_bytes()
                frame_count += 1
                logger.info(f"Frame {frame_count} recebido: {len(data)} bytes")
                
                # Converte os bytes recebidos em um frame numpy
                nparr = np.frombuffer(data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if frame is None:
                    logger.error("Erro ao decodificar o frame")
                    continue
                
                # Redimensiona o frame para melhor performance
                frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
                
                # Converte o frame para RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Encontra faces no frame
                face_locations = face_recognition.face_locations(rgb_frame, model="hog")
                logger.info(f"Frame {frame_count}: {len(face_locations)} faces encontradas")
                
                frame_results = []
                if face_locations:
                    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                    logger.info(f"Frame {frame_count}: {len(face_encodings)} encodings gerados")
                    
                    # Verifica cada face encontrada
                    for i, face_encoding in enumerate(face_encodings):
                        logger.info(f"Frame {frame_count}: Analisando face {i+1}...")
                        
                        # Calcula as distâncias para todas as faces de referência
                        face_distances = face_recognition.face_distance(reference_encodings, face_encoding)
                        best_match_index = np.argmin(face_distances)
                        min_distance = face_distances[best_match_index]
                        
                        logger.info(f"Frame {frame_count}: Menor distância encontrada: {min_distance:.4f} com {reference_names[best_match_index]}")
                        
                        # Usando um limiar de tolerância mais flexível
                        if min_distance < 0.65:
                            confidence = float(1 - min_distance)
                            logger.info(f"Frame {frame_count}: Match encontrado: {reference_names[best_match_index]} (confiança: {confidence:.2%})")
                            frame_results.append({
                                "status": "match",
                                "name": reference_names[best_match_index],
                                "confidence": confidence
                            })
                        else:
                            logger.info(f"Frame {frame_count}: Nenhum match confiável para face {i+1} (melhor distância: {min_distance:.4f})")
                            frame_results.append({
                                "status": "no_match",
                                "name": "unknown",
                                "confidence": 0.0
                            })
                else:
                    logger.debug(f"Frame {frame_count}: Nenhuma face encontrada")
                
                # Envia os resultados de volta para o cliente
                await websocket.send_json({
                    "frame_results": frame_results,
                    "faces_found": len(face_locations)
                })
                
            except Exception as e:
                logger.error(f"Erro ao processar frame {frame_count}: {str(e)}", exc_info=True)
                continue
            
    except Exception as e:
        logger.error(f"Erro no WebSocket: {str(e)}", exc_info=True)
        await websocket.send_json({
            "error": str(e)
        })
    finally:
        logger.info(f"Conexão WebSocket fechada. Total de frames processados: {frame_count}")
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    logger.info("Iniciando servidor...")
    uvicorn.run(
        app,
        host="10.100.0.40",  # IP específico
        port=8081,  # Porta específica
        log_level="debug"  # Aumentando o nível de log para debug
    )