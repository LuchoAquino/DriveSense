import numpy as np

class PlateTracker:
    """
    Clase para realizar un seguimiento básico de las placas de vehículos
    a lo largo de múltiples frames. Utiliza la superposición (IoU) para
    asociar detecciones nuevas con placas ya trackeadas.
    """
    def __init__(self, iou_threshold=0.5, max_frames_without_detection=5):
        """
        Inicializa el rastreador de placas.

        Args:
            iou_threshold (float): Umbral de IoU para considerar que dos cajas son la misma placa.
            max_frames_without_detection (int): Número máximo de frames que una placa puede
                                                estar sin ser detectada antes de ser eliminada.
        """
        self.next_plate_id = 0
        self.tracked_plates = {}
        self.iou_threshold = iou_threshold
        self.max_frames_without_detection = max_frames_without_detection

    def _calculate_iou(self, box1, box2):
        """
        Calcula la Intersection over Union (IoU) de dos cajas delimitadoras.
        box: [x1, y1, x2, y2]
        """
        # Determinar las coordenadas de la intersección
        x_left = max(box1[0], box2[0])
        y_top = max(box1[1], box2[1])
        x_right = min(box1[2], box2[2])
        y_bottom = min(box1[3], box2[3])

        # Calcular el área de intersección
        intersection_area = max(0, x_right - x_left) * max(0, y_bottom - y_top)

        # Calcular el área de ambas cajas
        box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
        box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])

        # Calcular el área de unión
        union_area = float(box1_area + box2_area - intersection_area)

        # Evitar división por cero
        if union_area == 0:
            return 0.0

        return intersection_area / union_area

    def update(self, detections):
        """
        Actualiza el estado del rastreador con las nuevas detecciones.

        Args:
            detections (list): Lista de tuplas, donde cada tupla es
                               (bbox, confidence, plate_roi_image).
                               bbox: [x1, y1, x2, y2] de la placa.
                               confidence: Confianza de la detección de la placa.
                               plate_roi_image: La imagen recortada de la ROI de la placa.
        Returns:
            list: Lista de tuplas (plate_id, bbox, confidence, plate_roi_image, ocr_readings).
                  ocr_readings es una lista de tuplas (text, confidence) para esa placa.
        """
        updated_tracked_plates = {}
        assigned_detection_indices = set()

        # 1. Intentar asociar detecciones nuevas con placas trackeadas existentes
        for plate_id, plate_info in self.tracked_plates.items():
            best_match_iou = -1
            best_match_idx = -1

            for i, (new_bbox, new_conf, new_roi) in enumerate(detections):
                if i in assigned_detection_indices: # Ya asignada
                    continue

                iou = self._calculate_iou(plate_info['bbox'], new_bbox)
                if iou > self.iou_threshold and iou > best_match_iou:
                    best_match_iou = iou
                    best_match_idx = i
            
            if best_match_idx != -1:
                # Actualizar placa trackeada existente
                matched_bbox, matched_conf, matched_roi = detections[best_match_idx]
                plate_info['bbox'] = matched_bbox
                plate_info['confidence'] = matched_conf
                plate_info['plate_roi_image'] = matched_roi
                plate_info['frames_without_detection'] = 0
                updated_tracked_plates[plate_id] = plate_info
                assigned_detection_indices.add(best_match_idx)
            else:
                # Incrementar contador de frames sin detección
                plate_info['frames_without_detection'] += 1
                if plate_info['frames_without_detection'] <= self.max_frames_without_detection:
                    updated_tracked_plates[plate_id] = plate_info

        # 2. Añadir nuevas detecciones como nuevas placas trackeadas
        for i, (new_bbox, new_conf, new_roi) in enumerate(detections):
            if i not in assigned_detection_indices:
                new_plate_id = self.next_plate_id
                self.next_plate_id += 1
                updated_tracked_plates[new_plate_id] = {
                    'bbox': new_bbox,
                    'confidence': new_conf,
                    'plate_roi_image': new_roi,
                    'frames_without_detection': 0,
                    'ocr_readings': [] # Lista para almacenar lecturas de OCR
                }
        
        self.tracked_plates = updated_tracked_plates

        # Devolver las placas trackeadas activas para procesamiento posterior
        active_plates_for_processing = []
        for plate_id, plate_info in self.tracked_plates.items():
            if plate_info['frames_without_detection'] == 0: # Solo las que fueron detectadas en este frame
                active_plates_for_processing.append((plate_id, 
                                                     plate_info['bbox'], 
                                                     plate_info['confidence'], 
                                                     plate_info['plate_roi_image'],
                                                     plate_info['ocr_readings']))
        return active_plates_for_processing

    def get_tracked_plates(self):
        """
        Retorna todas las placas que están siendo trackeadas actualmente.
        """
        return self.tracked_plates
