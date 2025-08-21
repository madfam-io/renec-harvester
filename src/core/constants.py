"""Core constants for RENEC harvester."""

# Base URLs - Updated with verified working URLs
RENEC_BASE_URL = "https://conocer.gob.mx/RENEC"
CONOCER_BASE_URL = "https://conocer.gob.mx"

# Component types and URL patterns
COMPONENT_TYPES = {
    "ec_standard": ["estandar", "competencia", "/ec/", "estandares-de-competencia"],
    "certificador": ["certificador", "entidad", "/oec/", "organismos-certificadores"],
    "center": ["centro", "evaluacion", "/ce/", "centros-evaluacion"],
    "course": ["curso", "capacitacion", "formacion"],
    "evaluator": ["evaluador", "evaluadores"],
}

# Known working endpoints (verified August 2025)
RENEC_ENDPOINTS = {
    "ir_hub": [
        "/controlador.do?comp=IR",  # Main IR hub - VERIFIED WORKING
    ],
    "ec_standard": [
        "/controlador.do?comp=EC",  # EC Standards - VERIFIED WORKING 
        "/controlador.do?comp=EC&accion=consultar",
        "/controlador.do?comp=EC&accion=buscar",
    ],
    "certificador": [
        "/controlador.do?comp=CE",  # Certificadores - likely working
        "/controlador.do?comp=OEC", # Organismos Certificadores
        "/controlador.do?comp=ECE", # Entidades de Certificación
    ],
    "center": [
        "/controlador.do?comp=CA",  # Centros de Evaluación - guessed
        "/controlador.do?comp=CE", 
    ],
    "course": [
        "/controlador.do?comp=CO",  # Courses - guessed
        "/controlador.do?comp=OF",  # Oferta educativa
    ],
}

# XPath selectors by component type
XPATH_SELECTORS = {
    "ec_standard": {
        "container": "//div[@class='estandar-item' or contains(@class, 'ec-item')]",
        "code": ".//span[@class='ec-code' or contains(text(), 'EC')]",
        "title": ".//h3[@class='ec-title' or @class='titulo-estandar']",
        "sector": ".//span[@class='sector' or contains(@class, 'sector-productivo')]",
        "level": ".//span[@class='nivel' or contains(text(), 'Nivel')]",
        "publication_date": ".//span[@class='fecha' or contains(text(), 'Publicación')]",
    },
    "certificador": {
        "container": "//div[@class='oec-item' or contains(@class, 'certificador')]",
        "name": ".//h3[@class='oec-name' or @class='nombre']",
        "code": ".//span[@class='oec-code' or contains(text(), 'OC')]",
        "email": ".//a[contains(@href, 'mailto:')]",
        "phone": ".//span[@class='telefono' or contains(text(), 'Tel')]",
        "address": ".//div[@class='direccion' or @class='address']",
    },
    "center": {
        "container": "//div[@class='ce-item' or contains(@class, 'centro-evaluacion')]",
        "name": ".//h3[@class='ce-name' or @class='nombre']",
        "code": ".//span[@class='ce-code' or contains(text(), 'CE')]",
        "certificador": ".//span[@class='oec-parent' or contains(text(), 'OC')]",
        "email": ".//a[contains(@href, 'mailto:')]",
        "phone": ".//span[@class='telefono' or contains(text(), 'Tel')]",
        "address": ".//div[@class='direccion' or @class='address']",
    },
    "course": {
        "container": "//div[@class='curso-item' or contains(@class, 'course')]",
        "name": ".//h3[@class='curso-name' or @class='titulo']",
        "ec_code": ".//span[contains(text(), 'EC')]",
        "duration": ".//span[@class='duracion' or contains(text(), 'horas')]",
        "modality": ".//span[@class='modalidad' or contains(text(), 'Presencial') or contains(text(), 'Línea')]",
    },
}

# CSS selectors as fallback
CSS_SELECTORS = {
    "ec_standard": {
        "container": ".estandar-item, .ec-item",
        "code": ".ec-code",
        "title": ".ec-title, .titulo-estandar",
        "sector": ".sector, .sector-productivo",
        "level": ".nivel",
        "publication_date": ".fecha-publicacion",
    },
    "certificador": {
        "container": ".oec-item, .certificador",
        "name": ".oec-name, .nombre",
        "code": ".oec-code",
        "email": "a[href^='mailto:']",
        "phone": ".telefono",
        "address": ".direccion, .address",
    },
}

# Data validation patterns
VALIDATION_PATTERNS = {
    "ec_code": r"^EC\d{4}(\.\d{2})?$",
    "oec_code": r"^OC\d{3,4}$",
    "ce_code": r"^CE\d{4,5}$",
    "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    "phone": r"^[\d\s\-\+\(\)]+$",
    "rfc": r"^[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}$",
    "curp": r"^[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]\d$",
}

# Rate limiting configuration
RATE_LIMIT_CONFIG = {
    "default": {
        "requests": 120,
        "period": 60,  # seconds
    },
    "api": {
        "requests": 300,
        "period": 60,
    },
    "aggressive": {
        "requests": 60,
        "period": 60,
    },
}

# Export formats
EXPORT_FORMATS = ["json", "csv", "parquet", "excel"]

# Database schema version
SCHEMA_VERSION = "1.0.0"