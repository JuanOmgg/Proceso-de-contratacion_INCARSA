/**
 * mockData.js
 * Datos de ejemplo para poblar el dashboard mientras no hay backend.
 * Sustituir por llamadas fetch()/API cuando el servicio esté disponible.
 */

const MOCK_SOLICITUDES = [
  {
    id: "SOL-2026-0142",
    empresaOrigen: "INCARSA",
    contratista: "Andes Ingeniería S.A.S.",
    plantas: ["Planta Norte", "Planta Sur"],
    fechaIngreso: "2026-08-10",
    fechaSalida: "2026-08-15",
    estado: "APROBADO",
    diligenciadoPor: "Laura Gómez",
    nivelRiesgo: "Alto",
    actividad: "Mantenimiento de calderas industriales",
    vehiculos: [
      {
        tipo: "Camioneta",
        placa: "WQR-234",
        conductor: "Carlos Andrés Peña Ruiz",
        licencia_doc: "licencia_carlos_pena.pdf",
        documentos: [
          { tipo_doc: "SOAT", nombre_archivo: "soat_wqr234.pdf" },
          { tipo_doc: "Revisión Tecnomecánica", nombre_archivo: "tecno_wqr234.pdf" }
        ]
      }
    ],
    equipos: [{ marca: "Dell", modelo: "Latitude 5440", serie: "SN-88213" }],
    personas: [
      { item: 1, nombres: "Carlos Andrés Peña Ruiz", tipoDoc: "CC", numDoc: "1032456789", cargo: "Técnico de calderas", documento: "cedula_carlos.pdf" },
      { item: 2, nombres: "Diana Marcela Ríos Soto", tipoDoc: "CC", numDoc: "1098765432", cargo: "Supervisor HSE", documento: "cedula_diana.pdf" }
    ]
  },
  {
    id: "SOL-2026-0143",
    empresaOrigen: "INCARSA",
    contratista: "Electro Montajes del Caribe",
    plantas: ["Planta Cartagena"],
    fechaIngreso: "2026-08-12",
    fechaSalida: "2026-08-14",
    estado: "EN REVISIÓN",
    diligenciadoPor: "Jorge Mendieta",
    nivelRiesgo: "Medio",
    actividad: "Revisión de tablero eléctrico principal",
    vehiculos: [],
    equipos: [{ marca: "HP", modelo: "ProBook 440", serie: "SN-55210" }],
    personas: [
      { item: 1, nombres: "Miguel Ángel Torres", tipoDoc: "CC", numDoc: "1076543210", cargo: "Electricista certificado", documento: "cedula_miguel.pdf" }
    ]
  },
  {
    id: "SOL-2026-0144",
    empresaOrigen: "INCARSA",
    contratista: "Servicios Logísticos del Oriente",
    plantas: ["Planta Norte"],
    fechaIngreso: "2026-08-09",
    fechaSalida: "2026-08-09",
    estado: "ENVIADO",
    diligenciadoPor: "Laura Gómez",
    nivelRiesgo: "Bajo",
    actividad: "Entrega de insumos de bodega",
    vehiculos: [
      {
        tipo: "Camión",
        placa: "TRK-901",
        conductor: "Fabián Restrepo Cano",
        licencia_doc: "licencia_fabian_restrepo.pdf",
        documentos: [
          { tipo_doc: "SOAT", nombre_archivo: "soat_trk901.pdf" },
          { tipo_doc: "Tarjeta de Propiedad", nombre_archivo: "tarjeta_propiedad_trk901.pdf" }
        ]
      }
    ],
    equipos: [],
    personas: [
      { item: 1, nombres: "Fabián Restrepo Cano", tipoDoc: "CC", numDoc: "1045678123", cargo: "Conductor", documento: "cedula_fabian.pdf" }
    ]
  },
  {
    id: "SOL-2026-0145",
    empresaOrigen: "INCARSA",
    contratista: "Andes Ingeniería S.A.S.",
    plantas: ["Planta Sur", "Planta Cartagena"],
    fechaIngreso: "2026-08-18",
    fechaSalida: "2026-08-20",
    estado: "POR APROBAR",
    diligenciadoPor: "Jorge Mendieta",
    nivelRiesgo: "Alto",
    actividad: "Inspección de líneas de alta presión",
    vehiculos: [
      {
        tipo: "Camioneta",
        placa: "ABC-112",
        conductor: "Sandra Milena López",
        licencia_doc: "licencia_sandra_lopez.pdf",
        documentos: [
          { tipo_doc: "SOAT", nombre_archivo: "soat_abc112.pdf" }
        ]
      }
    ],
    equipos: [{ marca: "Lenovo", modelo: "ThinkPad T14", serie: "SN-77021" }],
    personas: [
      { item: 1, nombres: "Sandra Milena López", tipoDoc: "CC", numDoc: "1023456781", cargo: "Ingeniera de procesos", documento: "cedula_sandra.pdf" },
      { item: 2, nombres: "Andrés Felipe Ríos", tipoDoc: "CE", numDoc: "9988771", cargo: "Técnico mecánico", documento: "cedula_andres.pdf" }
    ]
  },
  {
    id: "SOL-2026-0146",
    empresaOrigen: "INCARSA",
    contratista: "Grupo Constructor del Sur",
    plantas: ["Planta Sur"],
    fechaIngreso: "2026-07-28",
    fechaSalida: "2026-07-30",
    estado: "RECHAZADO",
    diligenciadoPor: "Laura Gómez",
    nivelRiesgo: "Medio",
    actividad: "Adecuación de cubierta bodega 3",
    vehiculos: [],
    equipos: [],
    personas: [
      { item: 1, nombres: "Ricardo Salazar Prieto", tipoDoc: "CC", numDoc: "1067894523", cargo: "Maestro de obra", documento: "cedula_ricardo.pdf" }
    ]
  },
  {
    id: "SOL-2026-0147",
    empresaOrigen: "INCARSA",
    contratista: "Electro Montajes del Caribe",
    plantas: ["Planta Norte"],
    fechaIngreso: "2026-08-21",
    fechaSalida: "2026-08-22",
    estado: "APROBADO",
    diligenciadoPor: "Jorge Mendieta",
    nivelRiesgo: "Bajo",
    actividad: "Calibración de sensores de temperatura",
    vehiculos: [{ tipo: "Camioneta", placa: "ZXE-330" }],
    equipos: [{ marca: "Dell", modelo: "Latitude 3420", serie: "SN-91002" }],
    personas: [
      { item: 1, nombres: "Paula Andrea Vega", tipoDoc: "CC", numDoc: "1054321987", cargo: "Instrumentista", documento: "cedula_paula.pdf" }
    ]
  }
];

const MOCK_USUARIOS = [
  { id: 1, nombres: "Laura", apellidos: "Gómez Fernández", tipoDoc: "CC", numDoc: "1032987654", telefono: "3011234567", correo: "laura.gomez@incarsa.com", rol: "GESTOR DE DOCUMENTACIÓN", fechaCreacion: "2025-02-11" },
  { id: 2, nombres: "Jorge", apellidos: "Mendieta Ortiz", tipoDoc: "CC", numDoc: "1045677812", telefono: "3007654321", correo: "jorge.mendieta@incarsa.com", rol: "GESTOR DE DOCUMENTACIÓN", fechaCreacion: "2025-03-02" },
  { id: 3, nombres: "Camila", apellidos: "Rojas Beltrán", tipoDoc: "CC", numDoc: "1099887766", telefono: "3159876543", correo: "camila.rojas@incarsa.com", rol: "SST", fechaCreacion: "2024-11-19" },
  { id: 4, nombres: "David", apellidos: "Higuera Márquez", tipoDoc: "CC", numDoc: "1076554332", telefono: "3121122334", correo: "david.higuera@incarsa.com", rol: "GESCO", fechaCreacion: "2024-09-05" },
  { id: 5, nombres: "Valentina", apellidos: "Cárdenas Ruiz", tipoDoc: "CC", numDoc: "1088776655", telefono: "3187766554", correo: "valentina.cardenas@incarsa.com", rol: "SCR", fechaCreacion: "2025-01-27" }
];

const MOCK_SOLICITUDES_POR_MES = [
  { mes: "Mar", total: 18 },
  { mes: "Abr", total: 24 },
  { mes: "May", total: 21 },
  { mes: "Jun", total: 30 },
  { mes: "Jul", total: 27 },
  { mes: "Ago", total: 16 }
];

const MOCK_USUARIOS_POR_ROL = [
  { rol: "SST", total: 6 },
  { rol: "GESCO", total: 4 },
  { rol: "SCR", total: 3 },
  { rol: "GESTOR DE DOCUMENTACIÓN", total: 5 }
];
