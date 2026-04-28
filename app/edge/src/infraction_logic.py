import cv2
import numpy as np

def is_traffic_light_red(frame, roi_rect):
    """
    Determina si el semáforo está en rojo basándose en el color de la ROI.
    roi_rect: [x, y, w, h]
    """
    if not roi_rect or len(roi_rect) != 4:
        return False
        
    x, y, w, h = roi_rect
    # Asegurar que el ROI está dentro de los límites de la imagen
    h_img, w_img = frame.shape[:2]
    x = max(0, x)
    y = max(0, y)
    w = min(w, w_img - x)
    h = min(h, h_img - y)
    
    if w <= 0 or h <= 0:
        return False

    roi = frame[y:y+h, x:x+w]
    
    # Convertir a escala de grises para analizar luminosidad
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # Aplicar un pequeño desenfoque para evitar ruido puntual
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Encontrar el píxel más brillante en la ROI
    (minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(blurred)
    
    # Si no hay nada brillante (semáforo apagado o de noche sin luz), no es rojo
    if maxVal < 150:
        return False
        
    # maxLoc[1] es la coordenada Y del punto más brillante
    brightest_y = maxLoc[1]
    
    # Dividir la altura en 3 tercios
    third_height = h / 3.0
    
    # En un semáforo vertical estándar, el ROJO está en el tercio superior
    if brightest_y < third_height:
        return True # La luz encendida está arriba (Rojo)
    
    # Si está en el medio (Ámbar) o abajo (Verde), retorna False
    return False

def get_bottom_center(bbox):
    """
    Retorna el centro inferior del bounding box (x_min, y_min, x_max, y_max).
    """
    x_min, y_min, x_max, y_max = bbox
    return (int((x_min + x_max) / 2), int(y_max))

def is_vehicle_in_crosswalk(bbox, polygon):
    """
    Verifica si la base del vehículo está dentro del polígono del cruce peatonal.
    polygon: [[x1,y1], [x2,y2], ...]
    """
    if not polygon or len(polygon) < 3:
        return False
        
    bottom_center = get_bottom_center(bbox)
    pts = np.array(polygon, np.int32)
    
    # pointPolygonTest retorna 1 si está dentro, 0 si está en el borde, -1 si está fuera
    dist = cv2.pointPolygonTest(pts, bottom_center, False)
    return dist >= 0

def ccw(A, B, C):
    """ Función auxiliar para intersección de líneas """
    return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])

def intersect(A, B, C, D):
    """
    Retorna True si el segmento AB se intersecta con el segmento CD.
    """
    return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)

def did_vehicle_cross_stop_line(prev_pos, curr_pos, stop_line):
    """
    Verifica si el segmento entre prev_pos y curr_pos cruza la stop_line.
    stop_line: [[x1,y1], [x2,y2]]
    """
    if not stop_line or len(stop_line) != 2:
        return False
    if not prev_pos or not curr_pos:
        return False
        
    C = stop_line[0]
    D = stop_line[1]
    return intersect(prev_pos, curr_pos, C, D)

def evaluate_infractions(track_id, vehicle_info, vehicle_bbox, config, frame):
    """
    Evalúa la lógica de infracciones.
    Retorna None si no hay infracción, o un dict si la hay.
    """
    if not config:
        return None
        
    lanes = config.get("lanes", [])
    crosswalk_polygon = config.get("crosswalk_polygon", [])
    
    curr_pos = get_bottom_center(vehicle_bbox)
    
    # Manejar historial del vehículo
    if 'history' not in vehicle_info:
        vehicle_info['history'] = []
    
    vehicle_info['history'].append(curr_pos)
    # Mantener historial corto
    if len(vehicle_info['history']) > 10:
        vehicle_info['history'].pop(0)

    # 1. Semáforo Rojo (Cruce de línea de parada por carril)
    # Jerarquía: Primero evaluamos si se pasó la luz roja (la peor infracción)
    if len(vehicle_info['history']) >= 2:
        prev_pos = vehicle_info['history'][-2]
        
        for lane in lanes:
            traffic_light_roi = lane.get("traffic_light_roi", [])
            stop_line = lane.get("stop_line", [])
            
            if is_traffic_light_red(frame, traffic_light_roi):
                if did_vehicle_cross_stop_line(prev_pos, curr_pos, stop_line):
                    return {'has_infraction': True, 'rule_id': 2, 'type': 'Semaforo Rojo', 'details': f'Vehículo cruzó la línea de parada del {lane.get("name", "carril")} en rojo.'}

    # 2. Invasión de Cruce Peatonal
    # Para ser invasión, el vehículo debe estar DENTRO del cruce peatonal Y estar DETENIDO (velocidad nula)
    # Buscamos si ALGÚN semáforo de carril recto está en rojo.
    any_red = any(is_traffic_light_red(frame, lane.get("traffic_light_roi", [])) for lane in lanes)
    
    if any_red and is_vehicle_in_crosswalk(vehicle_bbox, crosswalk_polygon):
        # Calcular velocidad analizando el historial (distancia movida en los últimos 5 frames)
        if len(vehicle_info['history']) >= 5:
            # Posición hace 5 frames
            old_pos = vehicle_info['history'][-5]
            # Distancia Euclidiana
            dist = np.sqrt((curr_pos[0] - old_pos[0])**2 + (curr_pos[1] - old_pos[1])**2)
            
            # Si se movió muy poco (ej. menos de 5 píxeles en 5 frames), está detenido
            is_stopped = dist < 5.0
            if is_stopped:
                return {'has_infraction': True, 'rule_id': 3, 'type': 'Invasión Cruce Peatonal', 'details': 'Vehículo detenido sobre el cruce en luz roja.'}

    return None
