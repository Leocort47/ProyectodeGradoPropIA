import PropertyGrid from '../componentes/PropertyGrid'
import AriaChat from '../componentes/AriaChat'
import './futuristic.css'
import { useState } from 'react'
import PropertiesTable from '../componentes/PropertiesTable'


export default function App() {
  const [lastData, setLastData] = useState<any[]>([])

  // Capturar datos que cargue la tabla para alimentar ARIA
  const onRowsLoaded = (rows:any[]) => {
    setLastData(rows.map(r => ({
      title: r.Nombre || r.Tipo,
      price_text: r.Precio,
      location: r['Ubicación'],
      area_m2: r['Área (m²)'],
      bedrooms: r.Habitaciones,
      bathrooms: r.Baños,
      admin: r['Administración'],
      phone: r['Teléfonos'],
      link: r.Link
    })))
    return (
    <>
      {/* ... tu hero/ARIA ... */}
      <PropertiesTable />
    </>
  )
  }



  return (
    <div className="stage">
      <nav className="topbar">
        <div className="brand">PropIA</div>
        <div className="menu">
          <a>Inicio</a><a>IA Assistant</a><a>Automatización</a><a>Tecnología</a>
          <span className="chip on">IA Activa</span>
        </div>
      </nav>

      <header className="hero">
        <div className="hero-copy">
          <h1>El Futuro de la Búsqueda Inmobiliaria Autónoma</h1>
          <p>Nuestra IA autónoma revoluciona la búsqueda de propiedades en Colombia. Automatiza, analiza y recomienda en tiempo real para maximizar ganancias y minimizar tiempo.</p>
          <div className="stats">
            <div><strong>10h</strong><span>Búsqueda Tradicional</span></div>
            <div><strong>&lt; 2h</strong><span>Con PropIA</span></div>
            <div><strong>80%</strong><span>Tiempo Ahorrado</span></div>
          </div>
        </div>
        <div className="aria">
          <AriaChat data={lastData} />
        </div>
      </header>

      <main className="panel">
        <h2>Explorar propiedades (con imágenes)</h2>
        <PropertyGrid />

        <h2 style={{ marginTop:24 }}>Tabla detallada</h2>
        <p>Incluye Link, Nombre, Área (m²), Habitaciones, Baños, Precio, Administración, Teléfonos, Contacto y Descripción.</p>
        <PropertiesTable />
      </main>

      <footer className="foot">© 2025 PropIA · IA para el mercado inmobiliario en Colombia</footer>
    </div>
  )
}
