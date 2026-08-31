/**
 * mock-usuarios.js
 * Datos de ejemplo para el módulo de Usuarios.
 * TODO: reemplazar por llamadas al backend:
 *   GET    /api/roles
 *   GET    /api/usuarios
 *   POST   /api/usuarios
 *   PUT    /api/usuarios/:id
 *   DELETE /api/usuarios/:id
 * Debe cargarse antes de usuario-formulario.js y usuarios-listado.js.
 */

const MOCK_ROLES = [
  { id: 1, nombre: "Administrador" },
  { id: 2, nombre: "Supervisor de planta" },
  { id: 3, nombre: "Operario" },
  { id: 4, nombre: "Auditor de seguridad" }
];

// nota: "contrasena" no se expone nunca en el listado, solo se usa
// como marcador de que el usuario ya tiene una contraseña asignada.
const MOCK_USUARIOS = [
  { id: 1, nombres: "Laura", apellidos: "Gómez", tipo_documento: "CC", num_documento: "1032456789", num_telefono: "3001234567", correo: "laura.gomez@incarsa.com", id_rol: 1, is_active: true, fecha_creacion: "2026-01-12" },
  { id: 2, nombres: "Carlos", apellidos: "Restrepo", tipo_documento: "CC", num_documento: "1098765432", num_telefono: "3012345678", correo: "carlos.restrepo@incarsa.com", id_rol: 2, is_active: true, fecha_creacion: "2026-01-15" },
  { id: 3, nombres: "María", apellidos: "Pérez", tipo_documento: "CC", num_documento: "1076543210", num_telefono: "3023456789", correo: "maria.perez@incarsa.com", id_rol: 3, is_active: true, fecha_creacion: "2026-01-20" },
  { id: 4, nombres: "Andrés", apellidos: "Torres", tipo_documento: "CE", num_documento: "890234567", num_telefono: "3034567890", correo: "andres.torres@incarsa.com", id_rol: 3, is_active: false, fecha_creacion: "2026-01-22" },
  { id: 5, nombres: "Diana", apellidos: "Ramírez", tipo_documento: "CC", num_documento: "1054321098", num_telefono: "3045678901", correo: "diana.ramirez@incarsa.com", id_rol: 4, is_active: true, fecha_creacion: "2026-02-02" },
  { id: 6, nombres: "Jorge", apellidos: "Salazar", tipo_documento: "CC", num_documento: "1043210987", num_telefono: "3056789012", correo: "jorge.salazar@incarsa.com", id_rol: 2, is_active: true, fecha_creacion: "2026-02-08" },
  { id: 7, nombres: "Paula", apellidos: "Mendoza", tipo_documento: "TI", num_documento: "1099887766", num_telefono: "3067890123", correo: "paula.mendoza@incarsa.com", id_rol: 3, is_active: true, fecha_creacion: "2026-02-14" },
  { id: 8, nombres: "Felipe", apellidos: "Cárdenas", tipo_documento: "CC", num_documento: "1032109876", num_telefono: "3078901234", correo: "felipe.cardenas@incarsa.com", id_rol: 3, is_active: false, fecha_creacion: "2026-02-19" },
  { id: 9, nombres: "Camila", apellidos: "Vargas", tipo_documento: "CC", num_documento: "1021098765", num_telefono: "3089012345", correo: "camila.vargas@incarsa.com", id_rol: 1, is_active: true, fecha_creacion: "2026-02-25" },
  { id: 10, nombres: "Santiago", apellidos: "Morales", tipo_documento: "CC", num_documento: "1010987654", num_telefono: "3090123456", correo: "santiago.morales@incarsa.com", id_rol: 2, is_active: true, fecha_creacion: "2026-03-03" },
  { id: 11, nombres: "Valentina", apellidos: "Ospina", tipo_documento: "PA", num_documento: "AR7788990", num_telefono: "3101234567", correo: "valentina.ospina@incarsa.com", id_rol: 4, is_active: true, fecha_creacion: "2026-03-10" },
  { id: 12, nombres: "Esteban", apellidos: "Duarte", tipo_documento: "CC", num_documento: "1009876543", num_telefono: "3112345678", correo: "esteban.duarte@incarsa.com", id_rol: 3, is_active: true, fecha_creacion: "2026-03-18" },
  { id: 13, nombres: "Natalia", apellidos: "Rincón", tipo_documento: "CC", num_documento: "1008765432", num_telefono: "3123456789", correo: "natalia.rincon@incarsa.com", id_rol: 3, is_active: false, fecha_creacion: "2026-03-25" },
  { id: 14, nombres: "Ricardo", apellidos: "Peña", tipo_documento: "CC", num_documento: "1007654321", num_telefono: "3134567890", correo: "ricardo.pena@incarsa.com", id_rol: 2, is_active: true, fecha_creacion: "2026-04-02" }
];
