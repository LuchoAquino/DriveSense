import cv2
import json
import os
import argparse
import numpy as np

CONFIG_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'video_configs.json')

def load_configs():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_configs(configs):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(configs, f, indent=4)
    print(f"Configuración guardada en {CONFIG_FILE}")

class ROISelector:
    def __init__(self, frame, video_name):
        self.frame = frame.copy()
        self.display_frame = frame.copy()
        self.video_name = video_name
        self.configs = load_configs()
        
        self.lanes = []
        self.current_lane_idx = 0
        self.crosswalk_polygon = []
        
        self.current_mode = "traffic_light"
        self.drawing = False
        self.temp_point = None

        # Load existing if available
        if video_name in self.configs:
            cfg = self.configs[video_name]
            self.lanes = cfg.get("lanes", [])
            self.crosswalk_polygon = cfg.get("crosswalk_polygon", [])
            
        if not self.lanes:
            # Create at least one default lane
            self.lanes.append({"name": "Carril 1", "traffic_light_roi": [], "stop_line": []})

        cv2.namedWindow('ROI Selector', cv2.WINDOW_NORMAL)
        cv2.setMouseCallback('ROI Selector', self.mouse_callback)

    def draw_all(self):
        self.display_frame = self.frame.copy()
        
        # Draw Lanes
        colors = [(0, 0, 255), (0, 165, 255), (0, 255, 255), (255, 0, 255)] # Distintos colores para carriles
        
        for i, lane in enumerate(self.lanes):
            color = colors[i % len(colors)]
            thickness = 3 if i == self.current_lane_idx else 1
            
            # Draw Traffic Light ROI
            tl = lane.get("traffic_light_roi", [])
            if len(tl) == 4:
                x, y, w, h = tl
                cv2.rectangle(self.display_frame, (x, y), (x+w, y+h), color, thickness)
                cv2.putText(self.display_frame, f'Sem {i+1}', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness)

            # Draw Stop Line
            sl = lane.get("stop_line", [])
            if len(sl) == 1:
                pt1 = tuple(sl[0])
                cv2.circle(self.display_frame, pt1, 4, color, -1)
                cv2.putText(self.display_frame, f'Parada {i+1} (clic para fin)', pt1, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness)
            elif len(sl) == 2:
                pt1, pt2 = tuple(sl[0]), tuple(sl[1])
                cv2.line(self.display_frame, pt1, pt2, color, thickness)
                cv2.putText(self.display_frame, f'Parada {i+1}', pt1, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness)

        # Draw Crosswalk Polygon
        if len(self.crosswalk_polygon) > 0:
            pts = np.array(self.crosswalk_polygon, np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.polylines(self.display_frame, [pts], True, (255, 0, 0), 2)
            cv2.putText(self.display_frame, 'Cruce Peatonal', tuple(self.crosswalk_polygon[0]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

        # Draw Instructions
        instructions = [
            f"EDITANDO: Carril {self.current_lane_idx + 1} / {len(self.lanes)}",
            f"MODO ACTUAL: {self.current_mode.upper()}",
            "--- Controles ---",
            "1: Dibujar Semaforo (Arrastrar)",
            "2: Dibujar Linea Parada (Click inicio, Click fin)",
            "3: Dibujar Cruce Peatonal (Global) (Clicks)",
            "N: Nuevo Carril",
            "TAB: Cambiar de Carril",
            "R: Reiniciar modo actual en el carril actual",
            "S: Guardar y Salir",
            "Q: Salir sin guardar"
        ]
        for i, text in enumerate(instructions):
            # Borde negro para visibilidad
            cv2.putText(self.display_frame, text, (10, 20 + i*20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3)
            # Texto blanco principal
            cv2.putText(self.display_frame, text, (10, 20 + i*20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        cv2.imshow('ROI Selector', self.display_frame)

    def mouse_callback(self, event, x, y, flags, param):
        current_lane = self.lanes[self.current_lane_idx]
        
        if self.current_mode == "traffic_light":
            if event == cv2.EVENT_LBUTTONDOWN:
                self.drawing = True
                self.temp_point = (x, y)
            elif event == cv2.EVENT_MOUSEMOVE and self.drawing:
                self.draw_all()
                cv2.rectangle(self.display_frame, self.temp_point, (x, y), (0, 0, 255), 2)
                cv2.imshow('ROI Selector', self.display_frame)
            elif event == cv2.EVENT_LBUTTONUP:
                self.drawing = False
                x1, y1 = self.temp_point
                w, h = abs(x - x1), abs(y - y1)
                x_min, y_min = min(x1, x), min(y1, y)
                current_lane["traffic_light_roi"] = [x_min, y_min, w, h]
                self.draw_all()

        elif self.current_mode == "stop_line":
            if event == cv2.EVENT_LBUTTONDOWN:
                if len(current_lane["stop_line"]) >= 2:
                    current_lane["stop_line"] = [] # Autoreseteo si ya había una línea dibujada
                current_lane["stop_line"].append([x, y])
                self.draw_all()

        elif self.current_mode == "crosswalk":
            if event == cv2.EVENT_LBUTTONDOWN:
                self.crosswalk_polygon.append([x, y])
                self.draw_all()

    def run(self):
        self.draw_all()
        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == ord('1'):
                self.current_mode = "traffic_light"
                self.draw_all()
            elif key == ord('2'):
                self.current_mode = "stop_line"
                self.draw_all()
            elif key == ord('3'):
                self.current_mode = "crosswalk"
                self.draw_all()
            elif key == ord('n'):
                self.lanes.append({"name": f"Carril {len(self.lanes) + 1}", "traffic_light_roi": [], "stop_line": []})
                self.current_lane_idx = len(self.lanes) - 1
                self.draw_all()
            elif key == 9: # TAB
                self.current_lane_idx = (self.current_lane_idx + 1) % len(self.lanes)
                self.draw_all()
            elif key == ord('r'):
                if self.current_mode == "traffic_light":
                    self.lanes[self.current_lane_idx]["traffic_light_roi"] = []
                elif self.current_mode == "stop_line":
                    self.lanes[self.current_lane_idx]["stop_line"] = []
                elif self.current_mode == "crosswalk":
                    self.crosswalk_polygon = []
                self.draw_all()
            elif key == ord('s'):
                self.configs[self.video_name] = {
                    "lanes": self.lanes,
                    "crosswalk_polygon": self.crosswalk_polygon
                }
                save_configs(self.configs)
                break
            elif key == ord('q'):
                break
        cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seleccionador de ROI para Videos")
    parser.add_argument("--source", type=str, required=True, help="Ruta al video")
    args = parser.parse_args()

    if not os.path.exists(args.source):
        print(f"Error: El archivo {args.source} no existe.")
        exit(1)

    cap = cv2.VideoCapture(args.source)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        print("Error: No se pudo leer el video.")
        exit(1)

    video_basename = os.path.basename(args.source)
    print(f"Configurando ROIs para: {video_basename}")
    
    selector = ROISelector(frame, video_basename)
    selector.run()
