const BASE_URL = "http://127.0.0.1:8000";

export async function obtenerResidentes() {
  const respuesta = await fetch(`${BASE_URL}/residentes`);
  if (!respuesta.ok) {
    throw new Error("No se pudo obtener la lista de residentes");
  }
  return respuesta.json();
}

export async function obtenerLibro(residenteId = "") {
  const url = residenteId
    ? `${BASE_URL}/libro?residente_id=${encodeURIComponent(residenteId)}`
    : `${BASE_URL}/libro`;
  const respuesta = await fetch(url);
  if (!respuesta.ok) {
    throw new Error("No se pudo obtener el libro de incidencias");
  }
  return respuesta.json();
}

export async function enviarTriaje({ texto, residenteId, modo, proveedor, turno, fechaIncidente }) {
  const respuesta = await fetch(`${BASE_URL}/triaje`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      texto,
      residente_id: residenteId || null,
      modo,
      proveedor,
      turno,
      fecha_incidente: fechaIncidente,
    }),
  });

  const datos = await respuesta.json();

  if (!respuesta.ok) {
    const detalle = Array.isArray(datos.detail)
      ? datos.detail.map((d) => d.msg).join(", ")
      : datos.detail;
    throw new Error(detalle || "Error desconocido al triar la incidencia");
  }

  return datos;
}
export async function login(usuario, password) {
  const respuesta = await fetch(`${BASE_URL}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ usuario, password }),
  });
  const datos = await respuesta.json();
  if (!respuesta.ok) {
    throw new Error(datos.detail || "Usuario o contraseña incorrectos");
  }
  return datos;
}

export async function cambiarPassword({ usuario, passwordActual, passwordNueva, preguntaSecreta, respuestaSecreta }) {
  const respuesta = await fetch(`${BASE_URL}/cambiar-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      usuario,
      password_actual: passwordActual,
      password_nueva: passwordNueva,
      pregunta_secreta: preguntaSecreta || null,
      respuesta_secreta: respuestaSecreta || null,
    }),
  });
  const datos = await respuesta.json();
  if (!respuesta.ok) {
    throw new Error(datos.detail || "No se pudo cambiar la contraseña");
  }
  return datos;
}

export async function obtenerPreguntaSecreta(usuario) {
  const respuesta = await fetch(`${BASE_URL}/recuperar-password/pregunta?usuario=${encodeURIComponent(usuario)}`);
  const datos = await respuesta.json();
  if (!respuesta.ok) {
    throw new Error(datos.detail || "No se pudo obtener la pregunta secreta");
  }
  return datos.pregunta;
}

export async function restablecerPassword({ usuario, respuesta: respuestaSecreta, passwordNueva }) {
  const respuesta = await fetch(`${BASE_URL}/recuperar-password/restablecer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ usuario, respuesta: respuestaSecreta, password_nueva: passwordNueva }),
  });
  const datos = await respuesta.json();
  if (!respuesta.ok) {
    throw new Error(datos.detail || "No se pudo restablecer la contraseña");
  }
  return datos;
}