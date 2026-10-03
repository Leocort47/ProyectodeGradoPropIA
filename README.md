# ARIA — Búsqueda inteligente de propiedades en Colombia

Prototipo PropTech desarrollado como **trabajo de grado de Ingeniería de Sistemas (UNAB)**. ARIA automatiza la búsqueda de inmuebles para compra y arriendo en Colombia: extrae anuncios de varios portales inmobiliarios, los normaliza en una sola base de datos y responde búsquedas escritas en lenguaje natural.

> Caso de estudio completo en el portafolio: [leandro-cortes.com/projects/aria-proptech](https://www.leandro-cortes.com/projects/aria-proptech)

## Qué resuelve

Buscar vivienda en Colombia implica revisar varios portales con filtros, formatos y precios distintos. ARIA unifica esa información y responde a búsquedas como *"apartamento en arriendo en Cabecera con 2 habitaciones"* con resultados de todos los portales en un mismo lugar.

## Arquitectura

```
React + MUI (Vite)  ──►  FastAPI  ──►  PostgreSQL (asyncpg)
                            │
                            ├──► Scrapers (Selenium · BeautifulSoup · requests)
                            │      Finca Raíz · La Haus · Metrocuadrado
                            └──► Motor ARIA: consulta en lenguaje natural → filtros
```

- **Adaptadores por portal** (`backend/src/scrapers/adapters`): cada portal tiene su adaptador y todos devuelven el mismo esquema normalizado (precio, zona, área, habitaciones…).
- **Scraping resiliente**: `requests` y BeautifulSoup para páginas ligeras, y Selenium cuando el portal renderiza con JavaScript o tiene protección anti-bot.
- **Motor ARIA** (`backend/src/ai/aria_intelligence.py`): convierte una frase como *"apartamento en arriendo en Cabecera con 2 habitaciones hasta 2 millones"* en filtros estructurados (tipo, ciudad, barrio, habitaciones, baños, precio, área, garajes) y genera un resumen de la búsqueda.

## Stack

| Capa | Tecnologías |
| --- | --- |
| Frontend | React 18, TypeScript, Material UI, Vite, Axios |
| Backend | Python 3.11, FastAPI, Pydantic, Uvicorn |
| Datos | PostgreSQL (asyncpg), pandas |
| Scraping | Selenium, BeautifulSoup, lxml, requests |
| Infra | Docker Compose |

**Siguiente fase:** ranking de resultados con scikit-learn y cola de scraping con Redis + RQ (las dependencias ya están en `requirements.txt`).

## Endpoints principales

| Método | Ruta | Descripción |
| --- | --- | --- |
| GET | `/health` | Estado del servicio |
| GET | `/scrape/{portal}` | Scraping de un portal (`fincaraiz`, `lahaus`, `metrocuadrado`) |
| GET | `/scrape/todos` | Scraping unificado de todos los portales |
| POST | `/api/aria/search` | Búsqueda en lenguaje natural con ranking ARIA |
| GET | `/api/propiedades` | Propiedades guardadas en la base de datos |

La documentación interactiva queda disponible en `http://localhost:8000/docs` (Swagger de FastAPI).

## Ejecutar en local

Requisitos: Python 3.11, Node.js 20, PostgreSQL y Google Chrome (para Selenium).

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # completa los datos de tu base PostgreSQL
uvicorn src.main:app --reload --port 8000

# Frontend
cd frontend
cp .env.example .env
npm install
npm run dev
```

Con Docker: `docker compose -f docker/compose.yml up --build`.

## Estado

Prototipo académico en desarrollo (2025–2026). Los scrapers dependen de la estructura HTML de cada portal, así que pueden requerir ajustes cuando los sitios cambian.

## Autor

**Leandro Cortés** — Full Stack Developer · Ingeniería de Sistemas, UNAB (grado previsto: diciembre de 2026)
[Portafolio](https://www.leandro-cortes.com) · [LinkedIn](https://www.linkedin.com/in/leandro-cort%C3%A9s-6a0311191/) · leandrocort47@gmail.com
