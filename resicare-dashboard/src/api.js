const BASE_URL = "http://127.0.0.1:8000";

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
