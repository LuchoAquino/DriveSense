import cv2
from ultralytics import YOLO
import os
import numpy as np
import base64
from dotenv import load_dotenv
from infraction_logic import evaluate_infractions # Importar la función de lógica real
from collections import deque # Para el búfer de frames
import re # Para validación de formato de placa
import datetime # Para generar nombres de archivo únicos
import math # Para cálculos de frames
from database_manager import init_db, save_infraction_metadata, export_infractions_to_json # Importar funciones de la DB
import random
import time # Agregado para manejo de tiempo
import argparse # Para aceptar video fuente por consola
import json # Para leer configuraciones
import imageio # Para codificar H264 de forma nativa


import subprocess  # ya debe estar importado si no, agrégalo

def reencode_to_h264(input_path, output_path):
    """
    Función deprecada. Ahora se usa imageio para guardar directamente en H.264.
    """
    pass


# ================================
# CONFIGURACIÓN DE MODO
# ================================
MODE = "test"  # Cambiado a "test" para rendimiento fluido sin llamadas bloqueantes a OpenAI

if MODE == "real":
    from openai import OpenAI
    # Cargar variables del archivo .env
    load_dotenv()
    # Obtener la clave desde la variable de entorno
    api_key = os.getenv("OPENAI_API_KEY")
    # --- Configuración de OpenAI ---
    client = OpenAI(api_key=api_key)
    
    prompt_openai = """
    Extract the vehicle number plate text from the image.
    
    Respond in JSON format with:
    - "plate_text": the extracted plate text (or "None" if unable to extract)
    - "confidence": your confidence level as a decimal between 0.0 and 1.0
    
    Example response: {"plate_text": "A2B-345", "confidence": 0.85}
    
    Replace any non-English character with a dot (.)
    """

    def extract_text_openai(base64_encoded_data):
        """
        Envía una imagen codificada en base64 a la API de OpenAI para extraer texto.
        Retorna un diccionario con el texto y el nivel de confianza.
        """
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_openai},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_encoded_data}"},
                            },
                        ],
                    }
                ],
                max_tokens=100
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Limpiar el texto de respuesta eliminando etiquetas ```json si están presentes
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            
            # Intentar parsear como JSON
            try:
                import json
                result = json.loads(response_text)
                return {
                    'plate_text': result.get('plate_text', 'None'),
                    'confidence': float(result.get('confidence', 0.0))
                }
            except (json.JSONDecodeError, ValueError):
                # Si no es JSON válido, tratarlo como texto simple (fallback)
                print(f"[WARNING] Respuesta no es JSON válido, usando fallback: {response_text}")
                return {
                    'plate_text': response_text if response_text != "None" else "None",
                    'confidence': 0.5  # Confianza por defecto en caso de fallback
                }
                
        except Exception as e:
            print(f"Error al llamar a la API de OpenAI: {e}")
            return {
                'plate_text': "None",
                'confidence': 0.0
            }

def preprocess_plate_roi(plate_roi: np.ndarray) -> np.ndarray:
    """
    Aplica pre-procesamiento a la ROI de la placa para mejorar la precisión del OCR.
    """
    gray_roi = cv2.cvtColor(plate_roi, cv2.COLOR_BGR2GRAY)
    processed_roi = cv2.adaptiveThreshold(gray_roi, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                          cv2.THRESH_BINARY, 11, 2)
    return processed_roi

# def validate_peruvian_plate(plate_text: str) -> bool:
#     """
#     Valida si el texto de la placa cumple con el formato peruano (ej. A1B-234 o A1B-2345).
#     """
#     # Patrón para placas peruanas: 1 letra, 1 número, 1 letra, guion, 3 o 4 números
#     # Ejemplo: A1B-234 o A1B-2345
#     pattern = r"^[A-Z]\d[A-Z]-\d{3,4}$"
#     return re.match(pattern, plate_text) is not None

# def get_most_frequent_valid_plate(plate_readings: list) -> str:
#     """
#     Dada una lista de lecturas de placas, retorna la lectura más frecuente y válida.
#     """
#     valid_plates = [p for p in plate_readings if validate_peruvian_plate(p) and p != "None"]
#     if not valid_plates:
#         return "None"
    
#     # Contar la frecuencia de cada placa válida
#     from collections import Counter
#     plate_counts = Counter(valid_plates)
    
#     # Retornar la placa más común
#     most_common_plate = plate_counts.most_common(1)[0][0]
#     return most_common_plate

def create_thumbnail(image: np.ndarray, width: int = 320) -> np.ndarray:
    """
    Crea una miniatura (thumbnail) de una imagen manteniendo la relación de aspecto.

    Args:
        image (np.ndarray): La imagen original (frame de OpenCV).
        width (int): El ancho deseado para la miniatura.

    Returns:
        np.ndarray: La imagen redimensionada (miniatura).
    """
    h, w, _ = image.shape
    aspect_ratio = h / w
    height = int(width * aspect_ratio)
    thumbnail = cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)
    return thumbnail

def detect_vehicles_plates_and_ocr(vehicle_model_path: str, plate_model_path: str, video_source=0):
    """
    Captura video de la webcam, detecta vehículos y placas usando dos modelos YOLO,
    aplica OCR a las placas detectadas (usando OpenAI) y muestra los resultados en tiempo real.
    Optimizado para realizar OCR una sola vez por vehículo trackeado y solo si hay infracción.
    Incluye espera de 2 segundos antes del OCR para mejorar la estabilización de la imagen.
    """
    print(f"Cargando modelo YOLO para vehículos desde: {vehicle_model_path}")
    try:
        vehicle_model = YOLO(vehicle_model_path)
    except Exception as e:
        print(f"Error al cargar el modelo de vehículos: {e}")
        print("Asegúrate de que la ruta al modelo es correcta y el archivo existe.")
        return

    print(f"Cargando modelo YOLO para placas desde: {plate_model_path}")
    try:
        plate_model = YOLO(plate_model_path)
    except Exception as e:
        print(f"Error al cargar el modelo de placas: {e}")
        print("Asegúrate de que la ruta al modelo es correcta y el archivo existe.")
        return

    # Diccionario para almacenar la información de los vehículos procesados
    # Agregamos campos para manejo de tiempo y espera
    processed_vehicles_info = {}

    # Directorio para guardar las evidencias de infracciones
    # Raíz de app/ (2 niveles arriba de app/edge/src/)
    app_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    INFRACTIONS_SAVE_DIR = os.path.join(app_root, 'data', 'infractions_evidence')
    os.makedirs(INFRACTIONS_SAVE_DIR, exist_ok=True)

    # Determinar si la fuente es un string (ruta) o int (webcam)
    if isinstance(video_source, str) and video_source.isdigit():
        video_source = int(video_source)
        
    # Cargar la configuración del video
    config = None
    config_file = os.path.join(app_root, 'data', 'video_configs.json')
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            try:
                configs = json.load(f)
                video_basename = os.path.basename(str(video_source))
                config = configs.get(video_basename)
                if config:
                    print(f"[INFO] Configuración de ROIs cargada para {video_basename}")
                else:
                    print(f"[WARNING] No hay configuración de ROIs para {video_basename}.")
            except Exception as e:
                print(f"[ERROR] Al leer video_configs.json: {e}")
        
    print(f"[INFO] Inicializando captura desde: {video_source}")
    cap = cv2.VideoCapture(video_source)

    if not cap.isOpened():
        print(f"Error: No se pudo abrir la fuente de video {video_source}. Verifica la ruta o la webcam.")
        return

    # Obtener FPS y dimensiones del frame
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if fps == 0 or fps > 120: # Fallback en caso de que falle o de un valor ilógico
        fps = 30.0
    print(f"FPS fuente: {fps}, Dimensiones: {frame_width}x{frame_height}")

    # --- Configuración de Tiempos y Búferes ---
    PRE_INFRACTION_CONTEXT_SECONDS = 2.0
    POST_INFRACTION_CONTEXT_SECONDS = 5.0
    CLIP_DURATION_SECONDS = PRE_INFRACTION_CONTEXT_SECONDS + POST_INFRACTION_CONTEXT_SECONDS
    
    # Tiempo de espera antes del OCR para estabilización
    OCR_WAIT_TIME_SECONDS = 2.0

    total_clip_frames = int(CLIP_DURATION_SECONDS * fps)
    post_infraction_frames = int(POST_INFRACTION_CONTEXT_SECONDS * fps)

    # Búfer principal para almacenar los últimos frames del video.
    MAIN_FRAME_BUFFER_SIZE = total_clip_frames
    main_frame_buffer = deque(maxlen=MAIN_FRAME_BUFFER_SIZE)
    
    # Búfer para las ROIs de las placas detectadas (para OCR robusto)
    BUFFER_SIZE = 4 * int(fps) if fps > 0 else 120
    
    print(f"[INFO] Duración del clip: {CLIP_DURATION_SECONDS}s ({total_clip_frames} frames).")
    print(f"[INFO] Tiempo de espera para OCR: {OCR_WAIT_TIME_SECONDS}s para estabilización.")
    print(f"[INFO] Se esperarán {post_infraction_frames} frames ({POST_INFRACTION_CONTEXT_SECONDS}s) post-infracción para guardar.")

    print(f"\nDetección, OCR (modo {MODE.upper()}) y visualización iniciada. Presiona 'q' para salir.")

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: No se pudo leer el frame de la webcam. Saliendo...")
            break

        frame_count += 1
        current_time = time.time()

        # --- Detección y seguimiento de vehículos ---
        custom_tracker_path = os.path.join(app_root, 'edge', 'custom_tracker.yaml')
        vehicle_results = vehicle_model.track(frame, persist=True, tracker=custom_tracker_path, verbose=False)

        if vehicle_results[0].boxes and vehicle_results[0].boxes.id is not None:
            boxes = vehicle_results[0].boxes.xyxy.cpu().numpy()
            confidences = vehicle_results[0].boxes.conf.cpu().numpy()
            classes = vehicle_results[0].boxes.cls.cpu().numpy()
            track_ids = vehicle_results[0].boxes.id.int().cpu().numpy()

            for box, conf, cls, track_id in zip(boxes, confidences, classes, track_ids):
                vehicle_class_name = vehicle_model.names[int(cls)]
                vehicle_classes_of_interest = ['car', 'truck', 'bus', 'motorcycle']

                if vehicle_class_name in vehicle_classes_of_interest:
                    x1_v, y1_v, x2_v, y2_v = map(int, box)
                    vehicle_label = f"{vehicle_class_name} ID:{track_id}: {conf:.2f}"

                    cv2.rectangle(frame, (x1_v, y1_v), (x2_v, y2_v), (0, 255, 0), 2)
                    cv2.putText(frame, vehicle_label, (x1_v, y1_v - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                    # Inicializar información del vehículo si es nuevo
                    if track_id not in processed_vehicles_info:
                        processed_vehicles_info[track_id] = {
                            'infraction': None,
                            'plate_text': None,
                            'plate_roi_buffer': deque(maxlen=BUFFER_SIZE),
                            'saved_evidence': False,
                            # Nuevos campos para el guardado retardado
                            'is_recording_clip': False,
                            'infraction_frame_number': None,
                            'base_filename': None,
                            # Nuevos campos para manejo de tiempo de espera de OCR
                            'first_detection_time': current_time,
                            'ocr_ready': False,
                            'waiting_for_ocr': False,
                            'latest_plate_roi': None,  # Para almacenar la mejor ROI de placa
                            'ocr_confidence': 0.0,  # Inicializar con 0.0 en lugar de 0.9
                            'db_saved': False  # Nuevo campo para controlar guardado en DB
                        }
                        print(f"[INFO] Nuevo vehículo detectado ID {track_id}. Iniciando espera de {OCR_WAIT_TIME_SECONDS}s para estabilización.")

                    vehicle_info = processed_vehicles_info[track_id]

                    # Verificar si ya ha pasado el tiempo de espera para OCR
                    time_since_detection = current_time - vehicle_info['first_detection_time']
                    if not vehicle_info['ocr_ready'] and time_since_detection >= OCR_WAIT_TIME_SECONDS:
                        vehicle_info['ocr_ready'] = True
                        print(f"[INFO] Vehículo ID {track_id} listo para evaluación de infracciones.")

                    # --- Lógica de Infracción y OCR (Optimizada) ---
                    if vehicle_info['ocr_ready'] and vehicle_info['infraction'] is None and not vehicle_info['waiting_for_ocr']:
                        
                        # Evaluar infracción con lógica real
                        vehicle_bbox = [x1_v, y1_v, x2_v, y2_v]
                        infraction_status = evaluate_infractions(track_id, vehicle_info, vehicle_bbox, config, frame)
                        
                        if infraction_status is not None and infraction_status.get('has_infraction'):
                            vehicle_info['waiting_for_ocr'] = True
                            vehicle_info['infraction'] = infraction_status
                            print(f"\n¡INFRACCIÓN DETECTADA! Vehículo ID {track_id} - Tipo: {infraction_status['type']}")
                            print(f"[INFO] Buscando placa y procesando OCR...")
                            
                            # --- Detección de placas (SOLO CUANDO HAY INFRACCIÓN) ---
                            vehicle_roi = frame[y1_v:y2_v, x1_v:x2_v]
                            best_plate_roi = None
                            if vehicle_roi.shape[0] > 0 and vehicle_roi.shape[1] > 0:
                                plate_results = plate_model(vehicle_roi, stream=True, verbose=False)
                                for r_plate in plate_results:
                                    if r_plate.boxes:
                                        for p_box in r_plate.boxes:
                                            x1_p, y1_p, x2_p, y2_p = map(int, p_box.xyxy[0])
                                            # Dibujar la placa
                                            x1_p_abs, y1_p_abs = x1_p + x1_v, y1_p + y1_v
                                            x2_p_abs, y2_p_abs = x2_p + x1_v, y2_p + y1_v
                                            cv2.rectangle(frame, (x1_p_abs, y1_p_abs), (x2_p_abs, y2_p_abs), (255, 0, 0), 2)
                                            
                                            plate_roi = vehicle_roi[y1_p:y2_p, x1_p:x2_p]
                                            if plate_roi.shape[0] > 10 and plate_roi.shape[1] > 10:
                                                best_plate_roi = plate_roi.copy()
                                            break # Tomar solo la primera placa encontrada
                                    if best_plate_roi is not None:
                                        break
                            
                            # OCR según el modo
                            if MODE == "real" and best_plate_roi is not None:
                                # Modo real: usar OpenAI
                                processed_roi = preprocess_plate_roi(best_plate_roi)
                                _, buffer = cv2.imencode('.jpg', processed_roi)
                                base64_encoded = base64.b64encode(buffer).decode('utf-8')
                                ocr_result = extract_text_openai(base64_encoded)
                                final_plate_text = ocr_result['plate_text']
                                final_confidence = ocr_result['confidence']
                                print(f"  OCR Confidence: {final_confidence:.3f}")
                            else:
                                # Modo prueba o no se encontró placa
                                test_plates = ["A1B-123", "C2D-456", "E3F-789", "G4H-012"]
                                final_plate_text = random.choice(test_plates) if best_plate_roi is not None else "NO_PLATE"
                                final_confidence = 0.9 if best_plate_roi is not None else 0.0
                            
                            vehicle_info['plate_text'] = final_plate_text
                            vehicle_info['ocr_confidence'] = final_confidence
                            print(f"  Placa detectada: {final_plate_text}. Iniciando captura de {POST_INFRACTION_CONTEXT_SECONDS}s post-infracción.")

                            # Marcar para grabación en lugar de guardar el video inmediatamente
                            vehicle_info['is_recording_clip'] = True
                            vehicle_info['infraction_frame_number'] = frame_count
                            
                            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                            infraction_type = infraction_status['type'].replace(" ", "_")
                            # Usar solo la placa limpia para el nombre del archivo
                            base_filename = f"infraction_{timestamp}_ID{track_id}_{infraction_type}_{final_plate_text}"
                            vehicle_info['base_filename'] = base_filename

                            # Guardar el frame de la infracción
                            image_filename = os.path.join(INFRACTIONS_SAVE_DIR, f"{base_filename}.jpg")
                            cv2.imwrite(image_filename, frame)
                            print(f"  Frame de infracción guardado: {os.path.basename(image_filename)}")

                            # Crear y guardar el thumbnail
                            thumbnail_image = create_thumbnail(frame)
                            thumbnail_filename = os.path.join(INFRACTIONS_SAVE_DIR, f"{base_filename}_thumbnail.jpg")
                            cv2.imwrite(thumbnail_filename, thumbnail_image)
                            print(f"  Thumbnail guardado: {os.path.basename(thumbnail_filename)}")

                            # GUARDADO EN BASE DE DATOS EN TIEMPO REAL
                            if not vehicle_info['db_saved']:
                                print(f"  [DB] Guardando infracción en base de datos...")
                                video_filename = os.path.join(INFRACTIONS_SAVE_DIR, f"{base_filename}.mp4")
                                save_infraction_metadata(
                                    timestamp=timestamp,
                                    plate_number=final_plate_text,  # Solo la placa limpia
                                    camera_id=1,  # ID fijo para la cámara del prototipo
                                    rule_id=infraction_status['rule_id'],
                                    confidence=final_confidence,  # Usar el confidence de OpenAI
                                    image_path=image_filename,
                                    video_path=video_filename,
                                    thumbnail_path=thumbnail_filename
                                )
                                vehicle_info['db_saved'] = True
                                print(f"  [DB] Infracción guardada en base de datos para placa {final_plate_text}")
                        else:
                            vehicle_info['plate_text'] = "None" # Aún evaluando, pero sin infracción

                    # --- Lógica de visualización de texto ---
                    # Determinar posición del texto: usar la posición de la placa si existe, sino la del vehículo
                    text_x = x1_v
                    text_y = y2_v + 20
                    
                    if vehicle_info['ocr_ready']:
                        display_text = f"OCR: {vehicle_info['plate_text'] or 'Processing...'}"
                        if vehicle_info['infraction'] and vehicle_info['infraction']['has_infraction']:
                            display_text += f" | INF: {vehicle_info['infraction']['type']}"
                    else:
                        remaining_time = OCR_WAIT_TIME_SECONDS - time_since_detection
                        display_text = f"Estabilizando... {remaining_time:.1f}s"
                    
                    cv2.putText(frame, display_text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        # Añadir el frame actual al búfer principal, usando .copy() para seguridad
        main_frame_buffer.append(frame.copy())

        # --- Bucle de Guardado de Clips de Video (Post-Infracción) ---
        for track_id, info in list(processed_vehicles_info.items()):
            if info['is_recording_clip'] and not info['saved_evidence']:
                frames_since_infraction = frame_count - info['infraction_frame_number']
                if frames_since_infraction >= post_infraction_frames:
                    print(f"\nContexto post-infracción capturado para ID {track_id}. Guardando clip de video...")
                    
                    frames_to_save = list(main_frame_buffer)
                    if len(frames_to_save) < total_clip_frames:
                        print(f"  Advertencia: Buffer incompleto ({len(frames_to_save)}/{total_clip_frames} frames). El video podría ser más corto.")

                    video_filename = os.path.join(INFRACTIONS_SAVE_DIR, f"{info['base_filename']}.mp4")
                    try:
                        # Guardar directamente en H.264 usando imageio
                        writer = imageio.get_writer(video_filename, fps=fps, codec='libx264', format='FFMPEG')
                        for f in frames_to_save:
                            # OpenCV usa BGR, imageio espera RGB
                            rgb_frame = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
                            writer.append_data(rgb_frame)
                        writer.close()
                        print(f"  [✔] Clip de video de {CLIP_DURATION_SECONDS}s guardado en formato web (H.264): {os.path.basename(video_filename)}")
                    except Exception as e:
                        print(f"  [ERROR] No se pudo guardar el video con imageio: {e}")

                    info['saved_evidence'] = True
                    info['is_recording_clip'] = False

        # Dibujar ROIs en pantalla si existen
        if config:
            lanes = config.get("lanes", [])
            for lane in lanes:
                tl = lane.get("traffic_light_roi", [])
                if len(tl) == 4:
                    x, y, w, h = tl
                    # Determinar si está en rojo para pintar el cuadro rojo o verde
                    from infraction_logic import is_traffic_light_red
                    color = (0, 0, 255) if is_traffic_light_red(frame, tl) else (0, 255, 0)
                    cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                
                sl = lane.get("stop_line", [])
                if len(sl) == 2:
                    cv2.line(frame, tuple(sl[0]), tuple(sl[1]), (0, 255, 255), 2)
                    
            cw = config.get("crosswalk_polygon", [])
            if len(cw) > 0:
                pts = np.array(cw, np.int32).reshape((-1, 1, 2))
                cv2.polylines(frame, [pts], True, (255, 0, 0), 2)

        cv2.imshow('Vehicle, Plate, Infraction and Optimized OCR', frame)

        # Simular tiempo real si estamos leyendo un video de archivo
        # IMPORTANTE: Si es un video pre-grabado y queremos procesar rápido,
        # quitamos el sleep. Esto evita perder IDs en el rastreador.
        elapsed_processing_time = time.time() - current_time
        target_frame_time = 1.0 / fps
        # if elapsed_processing_time < target_frame_time:
        #     time.sleep(target_frame_time - elapsed_processing_time)

        # Usar waitKey con 1ms en lugar de target_frame_time para que reaccione rápido a la 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Tecla 'q' presionada. Saliendo.")
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Proceso finalizado.")
    # Exportar la metadata a JSON al finalizar el proceso
    export_infractions_to_json()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DriveSense Edge Processing")
    parser.add_argument("--source", type=str, default="0", help="Fuente de video (0 para webcam, ruta/a/video.mp4 para archivo)")
    args = parser.parse_args()

    # Inicializar la base de datos al iniciar el script
    init_db()

    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_root = os.path.abspath(os.path.join(current_dir, '..', '..'))

    vehicle_model_path = os.path.join(app_root, 'edge', 'models', 'yolov11n.pt')
    plate_model_path = os.path.join(app_root, 'edge', 'models', 'best.pt')

    detect_vehicles_plates_and_ocr(vehicle_model_path, plate_model_path, video_source=args.source)