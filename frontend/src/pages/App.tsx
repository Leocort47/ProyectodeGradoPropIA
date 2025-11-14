import PropertyGrid from '../componentes/PropertyGrid';
import AriaChat from '../componentes/AriaChat';
import PropertiesTable from '../componentes/PropertiesTable';
import './futuristic.css';
import { useState } from 'react';

export default function App() {
  const [activeTab, setActiveTab] = useState('comprar');

  // Función para manejar búsqueda
  const handleSearch = () => {
    const propertyType = (document.getElementById('property-type') as HTMLSelectElement)?.value;
    const city = (document.getElementById('city') as HTMLSelectElement)?.value;
    const neighborhood = (document.getElementById('neighborhood') as HTMLInputElement)?.value;
    const bedrooms = (document.getElementById('bedrooms') as HTMLSelectElement)?.value;

    console.log('Buscando propiedades con filtros:', {
      propertyType,
      city,
      neighborhood,
      bedrooms
    });
  };

  const handleQuickFilter = (text: string) => {
    const input = document.getElementById('neighborhood') as HTMLInputElement;
    if (input) input.value = text;
  };

  return (
    <div className="stage">
      {/* Header estilo Apple */}
      <header className="site-header">
        <div className="nav-container">
          <div className="logo">
            <i className="fas fa-robot"></i>
            <span>ARIA</span>
          </div>
          
          <div className="nav-links">
            <a href="#">Inicio</a>
            <a href="#featured">Propiedades</a>
            <a href="#ai">Cómo funciona</a>
            <a href="#automation">Tecnología</a>
            <a href="#contact">Contacto</a>
          </div>
          
          <div className="nav-actions">
            <a href="#search"><i className="fas fa-search"></i></a>
            <a href="#"><i className="fas fa-user"></i></a>
          </div>
        </div>
      </header>

      {/* Hero Section estilo Apple */}
      <section className="hero">
        <div className="container">
          <h1>ARIA</h1>
          <h2>El futuro de la búsqueda inmobiliaria en Colombia</h2>
          <p>Inteligencia artificial que encuentra tu propiedad ideal en tiempo récord</p>
          
          <div className="hero-actions">
            <a href="#search" className="btn btn-primary">Buscar Propiedades</a>
            <a href="#ai" className="btn btn-secondary">Conocer ARIA</a>
          </div>
        </div>
      </section>

      {/* Search Section estilo LaHaus */}
      <section className="search-section" id="search">
        <div className="container">
          <h2 className="section-title">Encuentra tu hogar ideal</h2>
          <p className="section-subtitle">ARIA analiza miles de propiedades para mostrarte solo las que se ajustan a tus necesidades</p>
          
          <div className="search-box">
            <div className="search-tabs">
              <div 
                className={`search-tab ${activeTab === 'comprar' ? 'active' : ''}`}
                onClick={() => setActiveTab('comprar')}
              >
                Comprar
              </div>
              <div 
                className={`search-tab ${activeTab === 'arrendar' ? 'active' : ''}`}
                onClick={() => setActiveTab('arrendar')}
              >
                Arrendar
              </div>
              <div 
                className={`search-tab ${activeTab === 'proyectos' ? 'active' : ''}`}
                onClick={() => setActiveTab('proyectos')}
              >
                Proyectos Nuevos
              </div>
            </div>
            
            <div className="search-filters">
              <div className="filter-group">
                <label htmlFor="property-type">Tipo de propiedad</label>
                <select id="property-type">
                  <option value="">Todos</option>
                  <option value="apartamento">Apartamento</option>
                  <option value="casa">Casa</option>
                  <option value="apartaestudio">Apartaestudio</option>
                  <option value="finca">Finca</option>
                  <option value="local">Local Comercial</option>
                </select>
              </div>
              
              <div className="filter-group">
                <label htmlFor="city">Ciudad</label>
                <select id="city">
                  <option value="">Todas</option>
                  <option value="bogota">Bogotá</option>
                  <option value="bogota">Bucaramanga</option>
                  <option value="medellin">Medellín</option>
                  <option value="cali">Cali</option>
                  <option value="barranquilla">Barranquilla</option>
                  <option value="cartagena">Cartagena</option>
                </select>
              </div>
              
              <div className="filter-group">
                <label htmlFor="neighborhood">Barrio/Zona</label>
                <input type="text" id="neighborhood" placeholder="Ej: Cabecera, El Poblado..." />
              </div>
              
              <div className="filter-group">
                <label htmlFor="bedrooms">Habitaciones</label>
                <select id="bedrooms">
                  <option value="">Cualquiera</option>
                  <option value="1">1</option>
                  <option value="2">2</option>
                  <option value="3">3</option>
                  <option value="4">4+</option>
                </select>
              </div>
            </div>
            
            <button className="search-button" onClick={handleSearch}>
              <i className="fas fa-search"></i>
              Buscar propiedades
            </button>
            
            <div className="quick-filters">
              <div className="quick-filter" onClick={() => handleQuickFilter('3 hab | Cabecera | casa')}>
                3 hab | Cabecera | casa
              </div>
              <div className="quick-filter" onClick={() => handleQuickFilter('apartaestudio en Cabecera con 2 hab')}>
                apartaestudio en Cabecera con 2 hab
              </div>
              <div className="quick-filter" onClick={() => handleQuickFilter('Apartamento en El Poblado')}>
                Apartamento en El Poblado
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Featured Properties estilo Metrocuadrado */}
      <section className="featured-section" id="featured">
        <div className="container">
          <h2 className="section-title">Propiedades Destacadas</h2>
          <p className="section-subtitle">Seleccionadas inteligentemente por ARIA según tendencias del mercado</p>
          <PropertyGrid />
        </div>
      </section>

      {/* AI Section estilo Apple */}
      <section className="ai-section" id="ai">
        <div className="container">
          <h2 className="section-title">Inteligencia Artificial Avanzada</h2>
          <p className="section-subtitle">ARIA utiliza tecnología de vanguardia para transformar tu experiencia inmobiliaria</p>
          
          <div className="ai-features">
            <div className="ai-feature">
              <div className="ai-icon">
                <i className="fas fa-brain"></i>
              </div>
              <h3>Análisis Predictivo</h3>
              <p>Predecimos tendencias del mercado y valoraciones con precisión superior al 95%</p>
            </div>
            
            <div className="ai-feature">
              <div className="ai-icon">
                <i className="fas fa-robot"></i>
              </div>
              <h3>Asistente Virtual 24/7</h3>
              <p>Conversaciones naturales en español para entender tus necesidades específicas</p>
            </div>
            
            <div className="ai-feature">
              <div className="ai-icon">
                <i className="fas fa-chart-line"></i>
              </div>
              <h3>Valuación Automatizada</h3>
              <p>Análisis de miles de datos para calcular el valor justo de mercado</p>
            </div>
          </div>
        </div>
      </section>

      {/* Automation Section */}
      <section className="automation-section" id="automation">
        <div className="container">
          <h2 className="section-title">Automatización Total</h2>
          <p className="section-subtitle">Procesos optimizados que ahorran tiempo y maximizan resultados</p>
          
          <div className="automation-cards">
            <div className="automation-card">
              <i className="fas fa-sync-alt"></i>
              <h3>Extracción de Datos</h3>
              <p>Recolección automática de información de múltiples fuentes en tiempo real</p>
            </div>
            
            <div className="automation-card">
              <i className="fas fa-images"></i>
              <h3>Procesamiento de Imágenes</h3>
              <p>Visión por computadora para analizar y categorizar automáticamente fotos de propiedades</p>
            </div>
            
            <div className="automation-card">
              <i className="fas fa-bell"></i>
              <h3>Alertas Inteligentes</h3>
              <p>Notificaciones automáticas cuando aparecen propiedades que coinciden con tus criterios</p>
            </div>
          </div>
        </div>
      </section>

      {/* Tabla de Propiedades */}
      <section className="panel">
        <div className="container">
          <h2>Tabla detallada de propiedades</h2>
          <p>Incluye Link, Nombre, Área (m²), Habitaciones, Baños, Precio, Administración, Teléfonos, Contacto y Descripción.</p>
          <PropertiesTable />
        </div>
      </section>

      {/* Chat con ARIA */}
      <section className="aria-chat-section">
        <div className="container">
          <h2 className="section-title">Consulta con ARIA</h2>
          <div className="aria-chat-container">
            <AriaChat />
          </div>
        </div>
      </section>

      {/* Footer estilo Apple */}
      <footer className="site-footer" id="contact">
        <div className="container">
          <div className="footer-content">
            <div className="footer-column">
              <h3>ARIA</h3>
              <p>El asistente inmobiliario inteligente que utiliza IA para transformar tu experiencia de búsqueda de propiedades en Colombia.</p>
            </div>
            
            <div className="footer-column">
              <h3>Descubrir</h3>
              <ul>
                <li><a href="#search">Buscar Propiedades</a></li>
                <li><a href="#">Vender Propiedad</a></li>
                <li><a href="#">Agentes Inmobiliarios</a></li>
                <li><a href="#">Blog</a></li>
              </ul>
            </div>
            
            <div className="footer-column">
              <h3>Ciudades</h3>
              <ul>
                <li><a href="#">Bogotá</a></li>
                <li><a href="#">Bucaramanga</a></li>
                <li><a href="#">Medellín</a></li>
                <li><a href="#">Cali</a></li>
                <li><a href="#">Barranquilla</a></li>
                <li><a href="#">Cartagena</a></li>
              </ul>
            </div>
            
            <div className="footer-column">
              <h3>Contacto</h3>
              <ul>
                <li><i className="fas fa-phone"></i> +57 1 234 5678</li>
                <li><i className="fas fa-envelope"></i> info@aria.com.co</li>
                <li><i className="fas fa-map-marker-alt"></i> Bogotá, Colombia</li>
              </ul>
            </div>
          </div>
          
          <div className="copyright">
            <p>Copyright © 2025 ARIA - Asistente Inmobiliario Inteligente. Todos los derechos reservados.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}