"""
Pydantic models for API requests and responses.
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class SpiderMode(str, Enum):
    CRAWL = "crawl"
    HARVEST = "harvest"


class SpiderStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class ComponentSettings(BaseModel):
    ec_standards: bool = True
    certificadores: bool = True
    evaluation_centers: bool = True
    courses: bool = True
    sectors: bool = True
    committees: bool = False


class SpiderConfig(BaseModel):
    mode: SpiderMode = SpiderMode.CRAWL
    max_depth: int = Field(default=5, ge=1, le=10)
    concurrent_requests: int = Field(default=8, ge=1, le=20)
    download_delay: float = Field(default=0.5, ge=0.0, le=5.0)
    retry_times: int = Field(default=3, ge=0, le=10)
    respect_robots_txt: bool = True
    enable_caching: bool = True
    target_components: ComponentSettings = ComponentSettings()


class SpiderStats(BaseModel):
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    items_scraped: int = 0
    current_speed: float = 0.0  # items per minute
    avg_response_time: float = 0.0  # milliseconds
    queue_size: int = 0
    uptime: str = "00:00:00"
    status: SpiderStatus = SpiderStatus.IDLE
    start_time: Optional[datetime] = None
    last_activity: Optional[datetime] = None


class SpiderResponse(BaseModel):
    success: bool
    message: str
    status: SpiderStatus
    config: Optional[SpiderConfig] = None


class DataItem(BaseModel):
    id: str
    type: str
    title: str
    code: str
    sector: Optional[str] = None
    last_updated: datetime
    status: str
    data: Optional[Dict[str, Any]] = None


class DataResponse(BaseModel):
    items: List[DataItem]
    total: int
    page: int = 1
    per_page: int = 50


class ExportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"


class SystemHealth(BaseModel):
    database: str = "unknown"
    redis: str = "unknown"
    spider: str = "unknown"
    memory_usage: float = 0.0
    disk_usage: float = 0.0


# Sprint 2 Models for new endpoints

# Pagination
class PaginationParams(BaseModel):
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=1000, description="Maximum records to return")


# EC Standard models
class ECStandardBase(BaseModel):
    ec_clave: str
    titulo: str
    version: Optional[str]
    vigente: bool
    sector: Optional[str]
    sector_id: Optional[int]
    nivel: Optional[str]
    duracion_horas: Optional[int]

class ECStandardResponse(ECStandardBase):
    last_seen: datetime

class ECStandardDetail(ECStandardBase):
    comite: Optional[str]
    comite_id: Optional[int]
    descripcion: Optional[str]
    competencias: Optional[List[str]]
    tipo_norma: Optional[str]
    fecha_publicacion: Optional[datetime]
    fecha_vigencia: Optional[datetime]
    perfil_evaluador: Optional[str]
    criterios_evaluacion: Optional[List[str]]
    renec_url: Optional[str]
    first_seen: datetime
    last_seen: datetime
    certificadores: Optional[List[Dict[str, Any]]]


# Certificador models
class CertificadorBase(BaseModel):
    cert_id: str
    tipo: str
    nombre_legal: str
    siglas: Optional[str]
    estatus: str
    estado: str
    estado_inegi: str
    municipio: Optional[str]
    telefono: Optional[str]
    correo: Optional[str]

class CertificadorResponse(CertificadorBase):
    last_seen: datetime

class CertificadorDetail(CertificadorBase):
    domicilio_texto: Optional[str]
    cp: Optional[str]
    sitio_web: Optional[str]
    representante_legal: Optional[str]
    fecha_acreditacion: Optional[datetime]
    contactos_adicionales: Optional[List[Dict[str, str]]]
    src_url: Optional[str]
    first_seen: datetime
    last_seen: datetime
    ec_standards: Optional[List[Dict[str, Any]]]


# Centro models
class CentroBase(BaseModel):
    centro_id: str
    nombre: str
    estado: str
    estado_inegi: str
    municipio: Optional[str]
    domicilio: Optional[str]
    telefono: Optional[str]
    correo: Optional[str]
    coordinador: Optional[str]

class CentroResponse(CentroBase):
    last_seen: datetime

class CentroDetail(CentroBase):
    extension: Optional[str]
    sitio_web: Optional[str]
    certificador_id: Optional[str]
    src_url: Optional[str]
    first_seen: datetime
    last_seen: datetime
    ec_standards: Optional[List[Dict[str, Any]]]
    certificador: Optional[Dict[str, Any]]


# Sector models
class SectorBase(BaseModel):
    sector_id: int
    nombre: str
    descripcion: Optional[str]

class SectorResponse(SectorBase):
    total_ec_standards: int
    last_seen: datetime

class SectorDetail(SectorBase):
    src_url: Optional[str]
    first_seen: datetime
    last_seen: datetime
    total_ec_standards: int
    total_comites: int
    comites: List[Dict[str, Any]]
    sample_ec_standards: List[Dict[str, Any]]


# Comite models
class ComiteBase(BaseModel):
    comite_id: int
    nombre: str
    sector_id: Optional[int]

class ComiteResponse(ComiteBase):
    sector_nombre: Optional[str]
    total_ec_standards: int
    last_seen: datetime

class ComiteDetail(ComiteBase):
    descripcion: Optional[str]
    institucion_representada: Optional[str]
    src_url: Optional[str]
    first_seen: datetime
    last_seen: datetime
    sector: Optional[Dict[str, Any]]
    total_ec_standards: int
    sample_ec_standards: List[Dict[str, Any]]