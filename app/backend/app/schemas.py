from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# Este es nuestro schema Pydantic. No es un modelo de base de datos (ORM),
# sino una herramienta para la validación y serialización de datos.
# Define la forma de los datos que se enviarán a través de la API.

class Infraction(BaseModel):
    """Define la estructura de una infracción para la API."""
    id: int
    timestamp: datetime
    plate_number: str
    camera_id: int
    rule_id: int
    rule_name: str # añadido para facilitar la identificación de la regla
    confidence: float
    status: str
    image_path: str
    video_path: str
    thumbnail_path: str
    # Campos faltantes para revisión
    review_decision: Optional[str] = None
    review_comments: Optional[str] = None
    reviewed_at: Optional[str] = None

    # Esta configuración permite que el modelo Pydantic se cree a partir de
    # un objeto de base de datos (ORM) o cualquier otro objeto arbitrario.
    class Config:
        from_attributes = True

class InfractionCountByRule(BaseModel):
    """Define la estructura para el conteo de infracciones por tipo de regla."""
    rule_name: str
    count: int

class InfractionCountByDay(BaseModel):
    """Define la estructura para el conteo de infracciones por día."""
    date: str  # Formato 'YYYY-MM-DD'
    count: int

class DashboardStats(BaseModel):
    """Define la estructura para las estadísticas generales del dashboard."""
    total_infractions: int
    pending_review: int
    confirmed: int
    rejected: int
    accuracy: float  # Porcentaje de confirmadas sobre el total revisado

class InfractionReview(BaseModel):
    """Define la estructura para la revisión de una infracción."""
    review_decision: str  # 'CONFIRMED' o 'REJECTED'
    review_comments: Optional[str] = None  # Comentarios opcionales del revisor
    plate_number: Optional[str] = None # Nuevo campo para el número de placa editado

class ReportRequest(BaseModel):
    infraction_ids: List[int]

class EmailRequest(BaseModel):
    recipient_email: str
    subject: str
    body: str
    infraction_ids: List[int]
