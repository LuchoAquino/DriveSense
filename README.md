# DriveSense 🚦

Sistema inteligente de detección automática de infracciones de tránsito.
Detecta vehículos en tiempo real con YOLOv8, lee placas con OCR (OpenAI GPT-4o-mini)
y expone un dashboard web (human-in-the-loop) para que un supervisor valide las infracciones.

---

## Estructura del Proyecto

```
.
├── training/               # Entrenamiento del modelo YOLO de detección de placas
│   ├── dataset/            # Dataset Roboflow (train / valid / test + data.yaml)
│   ├── models/
│   │   ├── base/           # Modelo base YOLO11n
│   │   └── runs/           # Experimentos de entrenamiento (train → train13)
│   ├── experiments/        # Resultados de pruebas (test_results.csv)
│   ├── train.py            # Script de entrenamiento
│   └── lpr_env.yml         # Entorno conda para entrenamiento
│
└── app/                    # Aplicación DriveSense
    ├── edge/               # Procesamiento en tiempo real (webcam/cámara)
    │   ├── src/            # Código fuente (vehicle_detector.py, database_manager.py, …)
    │   ├── models/         # Modelos en producción (best.pt, yolov11n.pt)
    │   └── utils/          # Utilidades (reencode_videos.py)
    ├── backend/            # API FastAPI
    │   ├── app/            # main.py, database.py, schemas.py
    │   └── scripts/        # Scripts de utilidad y migración de DB
    ├── frontend/           # Dashboard React + Vite
    │   └── src/            # Componentes, páginas, API client
    ├── data/               # Datos runtime [gitignored]
    │   ├── drivesense.db   # Base de datos SQLite
    │   ├── metadata.json   # Export JSON de la DB
    │   └── infractions_evidence/   # Videos y fotos de infracciones
    └── docs/               # Documentación, diagramas, reportes
```

---

## Cómo arrancar

### 1. Edge Processing (detección en tiempo real)

```bash
# Activar el entorno virtual
cd app
python -m venv venv
venv\Scripts\activate
pip install ultralytics opencv-python python-dotenv openai

# Asegúrate de tener el .env con OPENAI_API_KEY
# Ejecutar el detector
python app/edge/src/vehicle_detector.py
```

### 2. Backend (API FastAPI)

```bash
cd app/backend
# Activar venv (el mismo de arriba, o uno nuevo)
pip install -r requirements.txt
uvicorn app.main:app --reload
# API disponible en http://127.0.0.1:8000
# Docs en http://127.0.0.1:8000/docs
```

### 3. Frontend (Dashboard React)

```bash
cd app/frontend
npm install
npm run dev
# Dashboard en http://localhost:5173
```

---

## Variables de entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
OPENAI_API_KEY="sk-..."
# Opcional para envío de emails:
EMAIL_SENDER=""
EMAIL_PASSWORD=""
SMTP_SERVER=""
SMTP_PORT=587
```

---

## Estado actual del proyecto

| Componente | Estado |
|---|---|
| Modelo YOLO (detección de placas) | ✅ Entrenado (mAP50 = 97.4%) |
| Edge processing (detección + OCR) | ✅ Funcional |
| Detección de infracciones | ⚠️ Simulada aleatoriamente |
| Backend FastAPI | 🔴 Bug: código duplicado en main.py |
| Frontend dashboard | ✅ Visual completo (mock data) |
| Conexión frontend ↔ backend | 🔴 Pendiente |
| Deploy AWS | ⬜ No iniciado |

---

## Tecnologías

- **Edge:** Python, YOLOv8 (Ultralytics), OpenCV, OpenAI GPT-4o-mini
- **Backend:** FastAPI, SQLite, Pydantic, fpdf2
- **Frontend:** React, Vite, Material-UI, Recharts
- **Dataset:** Roboflow License Plate Recognition v11 (24k imágenes)
