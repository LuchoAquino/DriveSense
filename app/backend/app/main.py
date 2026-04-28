from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from typing import List
from fpdf import FPDF
import base64
import io
import os
from fastapi.responses import StreamingResponse
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware
import os
from fastapi.staticfiles import StaticFiles
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders


from . import schemas
from . import database

# Crear una instancia de la aplicación FastAPI
app = FastAPI(
    title="DriveSense API",
    description="La API para el sistema de detección de infracciones DriveSense.",
    version="0.1.0",
)

# Directorio donde se almacenan las evidencias de las infracciones
EVIDENCE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'infractions_evidence'))
print(f"Directorio de evidencias: {EVIDENCE_DIR}")

app.mount("/evidence", StaticFiles(directory=EVIDENCE_DIR), name="evidence")


# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Permite el origen de tu frontend
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Permite todas las cabeceras
    expose_headers=["Content-Range", "Accept-Ranges"]  # Agregar estas cabeceras

)

# Definir un endpoint para la raíz de la API
@app.get("/")
def read_root():
    """Devuelve un mensaje de bienvenida."""
    return {"message": "Bienvenido a la API de DriveSense"}

@app.get("/api/video/{infraction_id}")
async def get_video(infraction_id: int):
    """
    Sirve el archivo de video de una infracción específica.
    """
    conn = None
    try:
        conn = database.get_db_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="No se pudo establecer conexión con la base de datos.")
        
        cursor = conn.cursor()
        cursor.execute("SELECT video_path FROM infractions WHERE id = ?", (infraction_id,))
        result = cursor.fetchone()
        
        if not result or not result[0]:
            raise HTTPException(status_code=404, detail=f"Video para la infracción con ID {infraction_id} no encontrado.")
        
        video_filename = result[0]
        
        # Construir la ruta absoluta al archivo de video
        video_path = os.path.join(EVIDENCE_DIR, video_filename)
        print(f"Ruta del video: {video_path}")
        
        # Verificar si el archivo existe
        if not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail=f"Archivo de video no encontrado en la ruta: {video_path}")
        
        return FileResponse(
            video_path,
            media_type="video/mp4",
            headers={
                "Accept-Ranges": "bytes",
                "Content-Disposition": f'inline; filename="{video_filename}"'
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener el video: {e}")
    finally:
        if conn:
            conn.close()

@app.get("/api/infractions", response_model=List[schemas.Infraction])
def get_all_infractions():
    """
    Obtiene una lista de todas las infracciones de la base de datos.
    """
    conn = None
    try:
        conn = database.get_db_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="No se pudo establecer conexión con la base de datos.")
            
        cursor = conn.cursor()
        cursor.execute("""
            SELECT i.*, r.name AS rule_name
            FROM infractions i
            JOIN rules r ON i.rule_id = r.id
        """)
        infractions_rows = cursor.fetchall()

        # Pre-procesamiento de los datos antes de la validación
        infractions_data = []
        for row in infractions_rows:
            row_dict = dict(row)
            # Convierte el string del timestamp a un objeto datetime real
            try:
                row_dict['timestamp'] = datetime.strptime(row_dict['timestamp'], "%Y%m%d_%H%M%S")
            except (ValueError, TypeError):
                # Si el formato es inesperado o el valor es nulo, se puede asignar un valor por defecto o manejar el error
                # Por ahora, lo dejaremos como está y Pydantic podría fallar si es requerido, o podemos asignarle None si el campo es opcional.
                # Para este caso, si falla la conversión, lo mejor es saltar el registro o marcarlo.
                pass # Opcional: manejar el error de un timestamp mal formado
            infractions_data.append(row_dict)

        # Convierte las filas de la base de datos a un diccionario y luego valida con Pydantic
        infractions = [schemas.Infraction.model_validate(data) for data in infractions_data]
        return infractions

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ocurrió un error interno: {e}")
    finally:
        if conn:
            conn.close()

@app.get("/api/infractions/pending", response_model=List[schemas.Infraction])
def get_pending_infractions():
    """
    Obtiene una lista de todas las infracciones con estado 'PENDING_REVIEW'.
    """
    conn = None
    try:
        conn = database.get_db_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="No se pudo establecer conexión con la base de datos.")

        cursor = conn.cursor()
        cursor.execute("""
            SELECT i.*, r.name AS rule_name
            FROM infractions i
            JOIN rules r ON i.rule_id = r.id
            WHERE i.status = ?
        """, ('PENDING_REVIEW',))
        infractions_rows = cursor.fetchall()

        infractions_data = []
        for row in infractions_rows:
            row_dict = dict(row)
            try:
                row_dict['timestamp'] = datetime.strptime(row_dict['timestamp'], "%Y%m%d_%H%M%S")
            except (ValueError, TypeError):
                pass
            infractions_data.append(row_dict)

        infractions = [schemas.Infraction.model_validate(data) for data in infractions_data]
        return infractions

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ocurrió un error interno: {e}")
    finally:
        if conn:
            conn.close()

@app.get("/api/infractions/confirmed", response_model=List[schemas.Infraction])
def get_confirmed_infractions():
    """
    Obtiene una lista de todas las infracciones con estado 'CONFIRMED'.
    """
    conn = None
    try:
        conn = database.get_db_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="No se pudo establecer conexión con la base de datos.")

        cursor = conn.cursor()
        cursor.execute("""
            SELECT i.*, r.name AS rule_name
            FROM infractions i
            JOIN rules r ON i.rule_id = r.id
            WHERE i.status = ?
        """, ('CONFIRMED',))
        infractions_rows = cursor.fetchall()

        infractions_data = []
        for row in infractions_rows:
            row_dict = dict(row)
            try:
                row_dict['timestamp'] = datetime.strptime(row_dict['timestamp'], "%Y%m%d_%H%M%S")
            except (ValueError, TypeError):
                pass
            infractions_data.append(row_dict)

        infractions = [schemas.Infraction.model_validate(data) for data in infractions_data]
        return infractions

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ocurrió un error interno: {e}")
    finally:
        if conn:
            conn.close()

@app.get("/api/dashboard/stats", response_model=schemas.DashboardStats)
def get_dashboard_stats():
    """
    Obtiene estadísticas generales para el dashboard: total de infracciones,
    pendientes de revisión, confirmadas, rechazadas y precisión.
    """
    conn = None
    try:
        conn = database.get_db_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="No se pudo establecer conexión con la base de datos.")

        cursor = conn.cursor()

        # Total de infracciones
        cursor.execute("SELECT COUNT(*) FROM infractions")
        total_infractions = cursor.fetchone()[0]

        # Infracciones pendientes de revisión
        cursor.execute("SELECT COUNT(*) FROM infractions WHERE status = 'PENDING_REVIEW'")
        pending_review = cursor.fetchone()[0]

        # Infracciones confirmadas
        cursor.execute("SELECT COUNT(*) FROM infractions WHERE status = 'CONFIRMED'")
        confirmed = cursor.fetchone()[0]

        # Infracciones rechazadas
        cursor.execute("SELECT COUNT(*) FROM infractions WHERE status = 'REJECTED'")
        rejected = cursor.fetchone()[0]

        # Precisión (confirmadas / (confirmadas + rechazadas))
        total_reviewed = confirmed + rejected
        accuracy = (confirmed / total_reviewed) * 100 if total_reviewed > 0 else 0.0

        return schemas.DashboardStats(
            total_infractions=total_infractions,
            pending_review=pending_review,
            confirmed=confirmed,
            rejected=rejected,
            accuracy=round(accuracy, 2)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ocurrió un error interno: {e}")
    finally:
        if conn:
            conn.close()

@app.get("/api/dashboard/infractions_by_rule", response_model=List[schemas.InfractionCountByRule])
def get_infractions_by_rule():
    """
    Obtiene el conteo de infracciones agrupadas por tipo de regla.
    """
    conn = None
    try:
        conn = database.get_db_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="No se pudo establecer conexión con la base de datos.")

        cursor = conn.cursor()
        # Unir con la tabla 'rules' para obtener el nombre de la regla
        cursor.execute("""
            SELECT r.name AS rule_name, COUNT(i.id) AS count
            FROM infractions i
            JOIN rules r ON i.rule_id = r.id
            GROUP BY r.name
            ORDER BY count DESC
        """)
        results = cursor.fetchall()

        return [schemas.InfractionCountByRule(rule_name=row['rule_name'], count=row['count']) for row in results]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ocurrió un error interno: {e}")
    finally:
        if conn:
            conn.close()

@app.get("/api/dashboard/infractions_by_day", response_model=List[schemas.InfractionCountByDay])
def get_infractions_by_day():
    """
    Obtiene el conteo de infracciones por día para los últimos 7 días.
    """
    conn = None
    try:
        conn = database.get_db_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="No se pudo establecer conexión con la base de datos.")

        cursor = conn.cursor()
        
        # Calcular la fecha de hace 7 días
        seven_days_ago = datetime.now() - timedelta(days=7)
        seven_days_ago_str = seven_days_ago.strftime("%Y%m%d_000000") # Formato para comparar con timestamp en DB

        # Consulta para obtener el conteo de infracciones por día
        # Extraemos la parte de la fecha del timestamp (YYYYMMDD)
        cursor.execute("""
            SELECT SUBSTR(timestamp, 1, 8) AS date_str, COUNT(id) AS count
            FROM infractions
            WHERE timestamp >= ?
            GROUP BY date_str
            ORDER BY date_str ASC
        """, (seven_days_ago_str,))
        results = cursor.fetchall()

        # Formatear los resultados para el esquema Pydantic
        infractions_by_day = []
        for row in results:
            # Convertir 'YYYYMMDD' a 'YYYY-MM-DD' para el frontend
            formatted_date = f"{row['date_str'][:4]}-{row['date_str'][4:6]}-{row['date_str'][6:8]}"
            infractions_by_day.append(schemas.InfractionCountByDay(date=formatted_date, count=row['count']))
        
        return infractions_by_day

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ocurrió un error interno: {e}")
    finally:
        if conn:
            conn.close()

@app.put("/api/infractions/{infraction_id}/review")
def review_infraction(infraction_id: int, review: schemas.InfractionReview):
    """
    Actualiza el estado de una infracción a 'CONFIRMED' o 'REJECTED'
    basado en la revisión humana.
    """
    conn = None
    try:
        conn = database.get_db_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="No se pudo establecer conexión con la base de datos.")

        cursor = conn.cursor()

        # Verificar si la infracción existe y está pendiente de revisión
        cursor.execute("SELECT status FROM infractions WHERE id = ?", (infraction_id,))
        current_status = cursor.fetchone()

        if not current_status:
            raise HTTPException(status_code=404, detail=f"Infracción con ID {infraction_id} no encontrada.")
        if current_status[0] != 'PENDING_REVIEW':
            raise HTTPException(status_code=400, detail=f"La infracción con ID {infraction_id} ya ha sido revisada (estado actual: {current_status[0]}).")

        # Validar la decisión de revisión
        if review.review_decision not in ["CONFIRMED", "REJECTED"]:
            raise HTTPException(status_code=400, detail="La decisión de revisión debe ser 'CONFIRMED' o 'REJECTED'.")

        # Actualizar la infracción
        updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Formato para la base de datos
        cursor.execute(
            """
            UPDATE infractions
            SET status = ?, review_decision = ?, review_comments = ?, reviewed_at = ?, plate_number = COALESCE(?, plate_number)
            WHERE id = ?
            """,
            (review.review_decision, review.review_decision, review.review_comments, updated_at, review.plate_number, infraction_id)
        )
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=500, detail="No se pudo actualizar la infracción.")

        return {"message": f"Infracción {infraction_id} actualizada a {review.review_decision}."}

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ocurrió un error interno: {e}")
    finally:
        if conn:
            conn.close()



def generate_pdf_report(infractions):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    for i, infraction in enumerate(infractions):
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "REPORTE DE INFRACCIONES", 0, 1, "C")
        pdf.ln(10)

        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, f"CASO N {i + 1:02d}:", 0, 1, "L")
        pdf.ln(2)

        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 7, f"PLACA: {infraction['plate_number']}", 0, 1, "L")
        pdf.cell(0, 7, f"TIPO DE INFRACCION: {infraction['rule_name']}", 0, 1, "L")

        try:
            timestamp_dt = datetime.strptime(infraction['timestamp'], "%Y%m%d_%H%M%S")
            formatted_timestamp = timestamp_dt.strftime("%d/%m/%Y, %H:%M")
        except Exception:
            formatted_timestamp = str(infraction['timestamp'])
        pdf.cell(0, 7, f"FECHA Y HORA: {formatted_timestamp}", 0, 1, "L")
        pdf.cell(0, 7, f"COMENTARIO: {infraction['review_comments'] or 'N/A'}", 0, 1, "L")
        pdf.ln(5)

        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 7, "FOTO DE LA EVIDENCIA:", 0, 1, "L")
        pdf.ln(2)

        image_path = os.path.join(EVIDENCE_DIR, infraction['image_path'])
        if os.path.exists(image_path):
            try:
                x_center = (pdf.w - 150) / 2
                pdf.image(image_path, x=x_center, w=150, h=100)
            except Exception as e:
                pdf.set_text_color(255, 0, 0)
                pdf.cell(0, 10, f"Error imagen: {e}", 0, 1, "C")
                pdf.set_text_color(0, 0, 0)
        else:
            pdf.set_text_color(255, 0, 0)
            pdf.cell(0, 10, "Imagen no encontrada.", 0, 1, "C")
            pdf.set_text_color(0, 0, 0)

        if i < len(infractions) - 1:
            pdf.add_page()

    return pdf.output(dest='S').encode('latin1')


@app.post("/api/reports/generate-pdf")
async def generate_report_pdf(request: schemas.ReportRequest):
    conn = None
    try:
        conn = database.get_db_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="No se pudo conectar con la base de datos.")
        cursor = conn.cursor()
        placeholders = ','.join('?' * len(request.infraction_ids))
        query = f"""
            SELECT i.*, r.name AS rule_name
            FROM infractions i
            JOIN rules r ON i.rule_id = r.id
            WHERE i.id IN ({placeholders}) AND i.status = 'CONFIRMED'
        """
        cursor.execute(query, tuple(request.infraction_ids))
        rows = cursor.fetchall()
        data = []
        for row in rows:
            d = dict(row)
            if isinstance(d['timestamp'], datetime):
                d['timestamp'] = d['timestamp'].strftime("%Y%m%d_%H%M%S")
            data.append(d)
        if not data:
            raise HTTPException(status_code=404, detail="No hay infracciones confirmadas para esos IDs.")
        pdf_bytes = generate_pdf_report(data)
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=reporte_infracciones.pdf"}
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar el reporte: {e}")
    finally:
        if conn:
            conn.close()


@app.post("/api/reports/send-email")
async def send_report_email(email_request: schemas.EmailRequest):
    conn = None
    try:
        conn = database.get_db_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="No se pudo conectar con la base de datos.")
        cursor = conn.cursor()
        placeholders = ','.join('?' * len(email_request.infraction_ids))
        query = f"""
            SELECT i.*, r.name AS rule_name
            FROM infractions i
            JOIN rules r ON i.rule_id = r.id
            WHERE i.id IN ({placeholders}) AND i.status = 'CONFIRMED'
        """
        cursor.execute(query, tuple(email_request.infraction_ids))
        rows = cursor.fetchall()
        data = []
        for row in rows:
            d = dict(row)
            if isinstance(d['timestamp'], datetime):
                d['timestamp'] = d['timestamp'].strftime("%Y%m%d_%H%M%S")
            data.append(d)
        if not data:
            raise HTTPException(status_code=404, detail="No hay infracciones confirmadas para esos IDs.")
        pdf_bytes = generate_pdf_report(data)
        sender_email = os.getenv("EMAIL_SENDER")
        sender_password = os.getenv("EMAIL_PASSWORD")
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = int(os.getenv("SMTP_PORT", 587))
        if not all([sender_email, sender_password, smtp_server]):
            raise HTTPException(status_code=500, detail="Configuracion de correo incompleta.")
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email_request.recipient_email
        msg['Subject'] = email_request.subject
        msg.attach(MIMEBase('text', 'plain').set_payload(email_request.body))
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(pdf_bytes)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="reporte_infracciones.pdf"')
        msg.attach(part)
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return {"message": "Reporte enviado exitosamente."}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al enviar el correo: {e}")
    finally:
        if conn:
            conn.close()


@app.get("/api/evidence/list")
def list_evidence_files():
    try:
        files = os.listdir(EVIDENCE_DIR)
        video_files = [f for f in files if f.lower().endswith(('.mp4', '.avi', '.mov'))]
        return {"files": video_files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
