import cv2
from ultralytics import YOLO
import os
import numpy as np
import base64
from dotenv import load_dotenv
# from openai import OpenAI # Comentado para evitar consumo de tokens
from infraction_generator import generate_random_infraction # Importar la función de generación de infracciones
from collections import deque # Para el búfer de frames
import re # Para validación de formato de placa
import datetime # Para generar nombres de archivo únicos
import math # Para cálculos de frames
from database_manager import init_db, save_infraction_metadata, export_infractions_to_json # Importar funciones de la DB

# # Cargar variables del archivo .env
# load_dotenv()

# # Obtener la clave desde la variable de entorno
# # api_key = os.getenv("OPENAI_API_KEY")

# # --- Configuración de OpenAI ---
# # client = OpenAI(api_key=api_key)

# # prompt_openai = """
# # Extract the vehicle number plate text from the image.
# # The format is: one letter, one number, one letter, a dash, and three numbers (e.g., A2B-345).
# # Be careful not to confuse:
# # - The letter 'O' with the number '0'
# # - The letter 'I' with the number '1'
# # - The letter 'Z' with the number '2'
# # If you are not able to extract text, respond: None.
# # Only output the plate text.
# # Replace any non-English character with a dot (.)
# # """

# # def extract_text_openai(base64_encoded_data):
# #     """
# #     Envía una imagen codificada en base64 a la API de OpenAI para extraer texto.
# #     """
# #     try:
# #         response = client.chat.completions.create(
# #             model="gpt-4o-mini",
# #             messages=[
# #                 {
# #                     "role": "user",
# #                     "content": [
# #                         {"type": "text", "text": prompt_openai},
# #                         {
# #                             "type": "image_url",
# #                             "image_url": {"url": f"data:image/jpeg;base64,{base64_encoded_data}"},
# #                         },
# #                     ],
# #                 }
# #             ],
# #             max_tokens=50
# #         )
# #         return response.choices[0].message.content.strip()
# #     except Exception as e:
# #         print(f"Error al llamar a la API de OpenAI: {e}")
# #         return "None"


def preprocess_plate_roi(plate_roi: np.ndarray) -> np.ndarray:
    """
    Aplica pre-procesamiento a la ROI de la placa para mejorar la precisión del OCR.
    """
    gray_roi = cv2.cvtColor(plate_roi, cv2.COLOR_BGR2GRAY)
    processed_roi = cv2.adaptiveThreshold(gray_roi, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                          cv2.THRESH_BINARY, 11, 2)
    return processed_roi

def validate_peruvian_plate(plate_text: str) -> bool:
    """
    Valida si el texto de la placa cumple con el formato peruano (ej. A1B-234 o A1B-2345).
    """
    # Patrón para placas peruanas: 1 letra, 1 número, 1 letra, guion, 3 o 4 números
    # Ejemplo: A1B-234 o A1B-2345
    pattern = r"^[A-Z]\d[A-Z]-\d{3,4}$"
    return re.match(pattern, plate_text) is not None

def get_most_frequent_valid_plate(plate_readings: list) -> str:
    """
    Dada una lista de lecturas de placas, retorna la lectura más frecuente y válida.
    """
    valid_plates = [p for p in plate_readings if validate_peruvian_plate(p) and p != "None"]
    if not valid_plates:
        return "None"
    
    # Contar la frecuencia de cada placa válida
    from collections import Counter
    plate_counts = Counter(valid_plates)
    
    # Retornar la placa más común
    most_common_plate = plate_counts.most_common(1)[0][0]
    return most_common_plate

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

def detect_vehicles_plates_and_ocr(vehicle_model_path: str, plate_model_path: str):
    """
    Captura video de la webcam, detecta vehículos y placas usando dos modelos YOLO,
    aplica OCR a las placas detectadas (usando OpenAI) y muestra los resultados en tiempo real.
    Optimizado para realizar OCR una sola vez por vehículo trackeado y solo si hay infracción.
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
    # {track_id: {'infraction': {...}, 'plate_text': 'ABC123', 'plate_roi_buffer': deque, 'saved_evidence': False}}
    processed_vehicles_info = {}

    # Directorio para guardar las evidencias de infracciones
    INFRACTIONS_SAVE_DIR = os.path.join(project_root, 'infractions_evidence')
    os.makedirs(INFRACTIONS_SAVE_DIR, exist_ok=True)

    # Inicializar la captura de video desde la webcam
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: No se pudo abrir la webcam. Asegúrate de que esté conectada y no esté en uso.")
        return

    # Obtener FPS y dimensiones del frame de la webcam
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if fps == 0: # Fallback en caso de que cap.get(cv2.CAP_PROP_FPS) retorne 0
        fps = 30.0
    print(f"FPS de la webcam: {fps}, Dimensiones: {frame_width}x{frame_height}")

    # --- Configuración de Tiempos y Búferes ---
    PRE_INFRACTION_CONTEXT_SECONDS = 2.0
    POST_INFRACTION_CONTEXT_SECONDS = 5.0
    CLIP_DURATION_SECONDS = PRE_INFRACTION_CONTEXT_SECONDS + POST_INFRACTION_CONTEXT_SECONDS

    total_clip_frames = int(CLIP_DURATION_SECONDS * fps)
    post_infraction_frames = int(POST_INFRACTION_CONTEXT_SECONDS * fps)

    # Búfer principal para almacenar los últimos frames del video.
    MAIN_FRAME_BUFFER_SIZE = total_clip_frames
    main_frame_buffer = deque(maxlen=MAIN_FRAME_BUFFER_SIZE)
    
    # Búfer para las ROIs de las placas detectadas (para OCR robusto)
    BUFFER_SIZE = 4 * int(fps) if fps > 0 else 120
    
    print(f"[INFO] Duración del clip: {CLIP_DURATION_SECONDS}s ({total_clip_frames} frames).")
    print(f"[INFO] Se esperarán {post_infraction_frames} frames ({POST_INFRACTION_CONTEXT_SECONDS}s) post-infracción para guardar.")

    print("\nDetección, OCR (OpenAI optimizado) y visualización iniciada. Presiona 'q' para salir.")

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: No se pudo leer el frame de la webcam. Saliendo...")
            break

        frame_count += 1

        # --- Detección y seguimiento de vehículos ---
        vehicle_results = vehicle_model.track(frame, persist=True, tracker='bytetrack.yaml', verbose=False)

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
                            'base_filename': None
                        }

                    # --- Detección de placas dentro del ROI del vehículo ---
                    vehicle_roi = frame[y1_v:y2_v, x1_v:x2_v]
                    if vehicle_roi.shape[0] > 0 and vehicle_roi.shape[1] > 0:
                        plate_results = plate_model(vehicle_roi, stream=True, verbose=False)
                        for r_plate in plate_results:
                            if r_plate.boxes:
                                for p_box in r_plate.boxes:
                                    x1_p, y1_p, x2_p, y2_p = map(int, p_box.xyxy[0])
                                    x1_p_abs, y1_p_abs = x1_p + x1_v, y1_p + y1_v
                                    x2_p_abs, y2_p_abs = x2_p + x1_v, y2_p + y1_v
                                    
                                    cv2.rectangle(frame, (x1_p_abs, y1_p_abs), (x2_p_abs, y2_p_abs), (255, 0, 0), 2)

                                    # --- Lógica de Infracción y OCR Robusto ---
                                    if processed_vehicles_info[track_id]['infraction'] is None:
                                        infraction_status = generate_random_infraction()
                                        processed_vehicles_info[track_id]['infraction'] = infraction_status
                                        
                                        if infraction_status['has_infraction']:
                                            print(f"\n¡INFRACCIÓN DETECTADA! Vehículo ID {track_id} - Tipo: {infraction_status['type']}")
                                            
                                            final_plate_text = "ABC-123" # Simulación de OCR
                                            processed_vehicles_info[track_id]['plate_text'] = final_plate_text
                                            print(f"  Placa (simulada): {final_plate_text}. Iniciando captura de {POST_INFRACTION_CONTEXT_SECONDS}s post-infracción.")

                                            # Marcar para grabación en lugar de guardar el video inmediatamente
                                            processed_vehicles_info[track_id]['is_recording_clip'] = True
                                            processed_vehicles_info[track_id]['infraction_frame_number'] = frame_count
                                            
                                            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                                            infraction_type = infraction_status['type'] or "UNKNOWN"
                                            base_filename = f"infraction_{timestamp}_ID{track_id}_{infraction_type}_{final_plate_text}"
                                            processed_vehicles_info[track_id]['base_filename'] = base_filename

                                            # Guardar el frame de la infracción
                                            image_filename = os.path.join(INFRACTIONS_SAVE_DIR, f"{base_filename}.jpg")
                                            cv2.imwrite(image_filename, frame)
                                            print(f"  Frame de infracción guardado: {os.path.basename(image_filename)}")

                                            # Crear y guardar el thumbnail
                                            thumbnail_image = create_thumbnail(frame)
                                            thumbnail_filename = os.path.join(INFRACTIONS_SAVE_DIR, f"{base_filename}_thumbnail.jpg")
                                            cv2.imwrite(thumbnail_filename, thumbnail_image)
                                            print(f"  Thumbnail guardado: {os.path.basename(thumbnail_filename)}")
                                        else:
                                            processed_vehicles_info[track_id]['plate_text'] = "NO INFRACTION"

                                    # --- Lógica de visualización de texto ---
                                    display_text = f"OCR: {processed_vehicles_info[track_id]['plate_text'] or 'None'}"
                                    if processed_vehicles_info[track_id]['infraction'] and processed_vehicles_info[track_id]['infraction']['has_infraction']:
                                        display_text += f" | INF: {processed_vehicles_info[track_id]['infraction']['type']}"
                                    
                                    cv2.putText(frame, display_text, (x1_p_abs, y2_p_abs + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

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
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    out = cv2.VideoWriter(video_filename, fourcc, fps, (frame_width, frame_height))
                    for f in frames_to_save:
                        out.write(f)
                    out.release()
                    
                    print(f"  [✔] Clip de video de {CLIP_DURATION_SECONDS}s guardado: {os.path.basename(video_filename)}")

                    # Guardar metadata en la base de datos
                    image_filename = os.path.join(INFRACTIONS_SAVE_DIR, f"{info['base_filename']}.jpg")
                    thumbnail_filename = os.path.join(INFRACTIONS_SAVE_DIR, f"{info['base_filename']}_thumbnail.jpg")
                    save_infraction_metadata(
                        timestamp=info['base_filename'].split('_')[1] + '_' + info['base_filename'].split('_')[2],
                        plate_number=info['plate_text'],
                        camera_id=1,  # ID fijo para la cámara del prototipo
                        rule_id=info['infraction']['rule_id'],
                        confidence=0.9,  # Simulado por ahora
                        image_path=image_filename,
                        video_path=video_filename,
                        thumbnail_path=thumbnail_filename
                    )

                    info['saved_evidence'] = True
                    info['is_recording_clip'] = False

        cv2.imshow('Vehicle, Plate, Infraction and Optimized OCR', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Tecla 'q' presionada. Saliendo.")
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Proceso finalizado.")
    # Exportar la metadata a JSON al finalizar el proceso
    export_infractions_to_json()

if __name__ == "__main__":
    # Inicializar la base de datos al iniciar el script
    init_db()

    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
    
    vehicle_model_path = os.path.join(project_root, 'edge-processing', 'models', 'yolov11n.pt')
    plate_model_path = os.path.join(project_root, 'edge-processing', 'models', 'best.pt')

    detect_vehicles_plates_and_ocr(vehicle_model_path, plate_model_path)
