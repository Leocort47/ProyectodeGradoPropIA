# TG1 - Prototipo de Aplicación Web Basada en IA para Búsqueda de Propiedades en Colombia

Aplicación web que automatiza la búsqueda de propiedades para compra y arriendo en Colombia con scraping e IA. Ver instrucciones de instalación en secciones de Backend y Frontend. 

# TG1 - Aplicación Web IA para Búsqueda de Propiedades en Colombia

## Descripción
Prototipo que integra scraping de portales inmobiliarios (FincaRaíz) y un backend FastAPI con frontend React para buscar propiedades de compra/arriendo en Colombia.

## Requisitos
- Python 3.11
- Node.js 20
- Docker (opcional)
- PostgreSQL y Redis (opcional para etapas siguientes)

## Instalación rápida (local)
1. Backend
   - `cd backend`
   - `python -m venv venv && source venv/bin/activate` (Windows: `venv\\Scripts\\activate`)
   - `pip install -r requirements.txt`
   - `uvicorn src.main:app --reload --host 0.0.0.0 --port 8000`

2. Frontend
   - `cd frontend`
   - `npm install`
   - `npm start` (o `npm run dev` con Vite)

3. Docker (opcional)
   - En la raíz: `docker-compose up --build`

## Endpoints
- `GET /api/properties` listar propiedades de ejemplo con filtros
- `POST /api/scrape/fincaraiz?pages=2&negocio=arriendo` ejecuta scraping de FincaRaíz Bucaramanga

## Variables de entorno frontend
- `VITE_API_BASE_URL=http://localhost:8000`

## Estructura
