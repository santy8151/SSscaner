import { useEffect, useRef, useState, type FormEvent } from "react";
import { Bluetooth, Unplug, Save, Activity } from "lucide-react";
import { api } from "./api";

interface Characteristic extends EventTarget {
  value?: DataView;
  properties: { read: boolean; notify: boolean; indicate: boolean };
  readValue(): Promise<DataView>;
  startNotifications(): Promise<Characteristic>;
  stopNotifications(): Promise<Characteristic>;
}
interface GattServer {
  connected: boolean;
  connect(): Promise<GattServer>;
  disconnect(): void;
  getPrimaryService(
    uuid: string,
  ): Promise<{ getCharacteristic(uuid: string): Promise<Characteristic> }>;
}
interface BLEDevice extends EventTarget {
  id: string;
  name?: string;
  gatt?: GattServer;
}
type BluetoothNavigator = Navigator & {
  bluetooth?: {
    requestDevice(options: {
      acceptAllDevices: boolean;
      optionalServices: string[];
    }): Promise<BLEDevice>;
  };
};
type Configuration = {
  manufacturer: string;
  model: string;
  source_reference: string;
  service_uuid: string;
  characteristic_uuid: string;
  signal: string;
  unit: string;
  encoding: string;
  byte_order: string;
  byte_offset: number;
  scale: number;
  offset: number;
};
type Profile = {
  id: string;
  name: string;
  vehicle_id: string;
  configuration: Configuration;
};
type Reading = {
  id: string;
  value: number;
  unit: string;
  raw_hex: string;
  observed_at: string;
  validation_status: string;
};
export function BleConnections({
  token,
  vehicles,
  canWrite,
}: {
  token: string;
  vehicles: { id: string; name: string }[];
  canWrite: boolean;
}) {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [selected, setSelected] = useState("");
  const [readings, setReadings] = useState<Reading[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("DISCONNECTED");
  const [deviceName, setDeviceName] = useState("");
  const cleanup = useRef<() => void>(() => {});
  const mounted = useRef(true);
  const readOnce = useRef<null | (() => Promise<void>)>(null);
  const lastSent = useRef(0);
  const sending = useRef(false);
  const bluetooth = (navigator as BluetoothNavigator).bluetooth;
  const supported = !!bluetooth && window.isSecureContext;
  const profile = profiles.find((item) => item.id === selected);
  const connected = status === "CONNECTED";
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      cleanup.current();
    };
  }, []);
  useEffect(() => {
    let live = true;
    api<Profile[]>("/devices", token)
      .then((data) => {
        if (live) {
          setProfiles(data);
          setSelected(data[0]?.id || "");
        }
      })
      .catch((reason) => {
        if (live) setError(reason.message);
      });
    return () => {
      live = false;
    };
  }, [token]);
  useEffect(() => {
    if (!selected) return;
    let live = true;
    setReadings([]);
    api<Reading[]>(`/devices/${selected}/readings`, token)
      .then((data) => {
        if (live) setReadings(data);
      })
      .catch((reason) => {
        if (live) setError(reason.message);
      });
    return () => {
      live = false;
    };
  }, [selected, token]);
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const form = event.currentTarget;
    const fields = new FormData(form);
    const string = (name: string) => String(fields.get(name));
    const number = (name: string) => Number(fields.get(name));
    try {
      const row = await api<Profile>("/devices", token, {
        name: string("name"),
        vehicle_id: string("vehicle"),
        configuration: {
          manufacturer: string("manufacturer"),
          model: string("model"),
          source_reference: string("source"),
          service_uuid: string("service").toLowerCase(),
          characteristic_uuid: string("characteristic").toLowerCase(),
          signal: string("signal"),
          unit: string("unit"),
          encoding: string("encoding"),
          byte_order: string("endian"),
          byte_offset: number("byteOffset"),
          scale: number("scale"),
          offset: number("offset"),
        },
      });
      setProfiles((old) => [row, ...old]);
      setSelected(row.id);
      form.reset();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "No se pudo guardar");
    } finally {
      setBusy(false);
    }
  }
  async function connect() {
    if (!profile || !bluetooth) return;
    setBusy(true);
    setError("");
    setStatus("SELECTING_DEVICE");
    cleanup.current();
    try {
      const device = await bluetooth.requestDevice({
        acceptAllDevices: true,
        optionalServices: [profile.configuration.service_uuid],
      });
      if (!mounted.current) {
        device.gatt?.disconnect();
        return;
      }
      if (!device.gatt)
        throw new Error(
          "El dispositivo no expone GATT BLE. Bluetooth clásico requiere otro adaptador.",
        );
      setStatus("CONNECTING");
      setDeviceName(device.name || "Dispositivo BLE seleccionado");
      const disconnected = () => {
        if (mounted.current) setStatus("DISCONNECTED");
        readOnce.current = null;
      };
      device.addEventListener("gattserverdisconnected", disconnected);
      cleanup.current = () => {
        device.removeEventListener("gattserverdisconnected", disconnected);
        device.gatt?.disconnect();
        readOnce.current = null;
      };
      const server = await device.gatt.connect();
      if (!mounted.current) {
        cleanup.current();
        return;
      }
      const service = await server.getPrimaryService(
        profile.configuration.service_uuid,
      );
      const characteristic = await service.getCharacteristic(
        profile.configuration.characteristic_uuid,
      );
      if (!mounted.current) {
        cleanup.current();
        return;
      }
      const publish = async (value: DataView, force = false) => {
        if (sending.current || (!force && Date.now() - lastSent.current < 2000))
          return;
        const raw_hex = Array.from(
          new Uint8Array(value.buffer, value.byteOffset, value.byteLength),
          (byte) => byte.toString(16).padStart(2, "0"),
        ).join("");
        lastSent.current = Date.now();
        sending.current = true;
        try {
          const result = await api<Reading>(
            `/devices/${profile.id}/readings`,
            token,
            {
              origin: "CLIENT_BLE",
              raw_hex,
              observed_at: new Date().toISOString(),
              idempotency_key: crypto.randomUUID(),
            },
          );
          if (mounted.current)
            setReadings((old) => [result, ...old].slice(0, 50));
        } catch (reason) {
          if (mounted.current)
            setError(
              reason instanceof Error
                ? reason.message
                : "No se pudo guardar lectura",
            );
        } finally {
          sending.current = false;
        }
      };
      const notification = () => {
        if (characteristic.value) void publish(characteristic.value);
      };
      cleanup.current = () => {
        characteristic.removeEventListener(
          "characteristicvaluechanged",
          notification,
        );
        device.removeEventListener("gattserverdisconnected", disconnected);
        if (server.connected) {
          if (
            characteristic.properties.notify ||
            characteristic.properties.indicate
          )
            void characteristic.stopNotifications().catch(() => {});
          server.disconnect();
        }
        readOnce.current = null;
      };
      if (
        characteristic.properties.notify ||
        characteristic.properties.indicate
      ) {
        characteristic.addEventListener(
          "characteristicvaluechanged",
          notification,
        );
        await characteristic.startNotifications();
      }
      if (characteristic.properties.read) {
        readOnce.current = async () =>
          publish(await characteristic.readValue(), true);
      }
      if (
        !characteristic.properties.read &&
        !characteristic.properties.notify &&
        !characteristic.properties.indicate
      )
        throw new Error(
          "La característica no permite lectura ni notificaciones.",
        );
      if (!mounted.current) {
        cleanup.current();
        return;
      }
      setStatus("CONNECTED");
      if (readOnce.current) await readOnce.current();
    } catch (reason) {
      cleanup.current();
      if (mounted.current) {
        setStatus("DISCONNECTED");
        setError(
          reason instanceof Error
            ? reason.message
            : "Conexión cancelada o no disponible",
        );
      }
    } finally {
      if (mounted.current) setBusy(false);
    }
  }
  function disconnect() {
    cleanup.current();
    setStatus("DISCONNECTED");
    setDeviceName("");
  }
  return (
    <div className="ble-layout">
      <section className="panel">
        <div className="panel-head">
          <h2>
            <Bluetooth size={18} />
            Bluetooth / manómetros digitales
          </h2>
          <span className="badge">SOLO LECTURA</span>
        </div>
        <p className="muted">
          Este botón abre el selector real del navegador. No genera dispositivos
          ficticios. Cada modelo requiere UUID, formato y escala documentados.
        </p>
        {!supported && (
          <div className="error" role="status">
            Este navegador no expone Web Bluetooth. Abre la aplicación en Chrome
            o Edge compatible, en localhost o HTTPS, y comprueba el adaptador
            Bluetooth del equipo.
          </div>
        )}
        <label>
          Perfil de lectura
          <select
            value={selected}
            onChange={(event) => setSelected(event.target.value)}
            disabled={busy || connected}
          >
            <option value="" disabled>
              Configura un instrumento
            </option>
            {profiles.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
        </label>
        <div className="ble-status">
          <span className={connected ? "dot" : ""} />
          <strong>{status}</strong>
          <span>{deviceName || "Sin dispositivo conectado"}</span>
        </div>
        <div className="ble-actions">
          <button
            onClick={connect}
            disabled={!supported || !profile || busy || connected || !canWrite}
          >
            <Bluetooth size={15} />
            Conectar Bluetooth real
          </button>
          <button
            className="secondary"
            disabled={!connected}
            onClick={disconnect}
          >
            <Unplug size={15} />
            Desconectar
          </button>
          <button
            className="secondary"
            disabled={!connected || !readOnce.current || busy}
            onClick={async () => {
              setBusy(true);
              try {
                await readOnce.current?.();
              } catch (reason) {
                setError(
                  reason instanceof Error ? reason.message : "Lectura fallida",
                );
              } finally {
                setBusy(false);
              }
            }}
          >
            <Activity size={15} />
            Leer ahora
          </button>
        </div>
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        <p className="warning-copy">
          Mapeo manual no validado. La aplicación interpreta bytes según tu
          configuración; no certifica la calibración del manómetro. Conserva la
          referencia absoluta o manométrica de la presión.
        </p>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>HORA</th>
                <th>VALOR</th>
                <th>BYTES RAW</th>
              </tr>
            </thead>
            <tbody>
              {readings.map((reading) => (
                <tr key={reading.id}>
                  <td>
                    {new Date(reading.observed_at).toLocaleTimeString("es-CO")}
                  </td>
                  <td>
                    {reading.value} {reading.unit}
                  </td>
                  <td className="mono raw-bytes">{reading.raw_hex}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!readings.length && (
          <p className="empty">
            Sin paquetes recibidos. Las lecturas reales se mantienen separadas
            de SAMPLE.
          </p>
        )}
      </section>
      <form className="panel" onSubmit={save}>
        <div className="panel-head">
          <h2>Configurar instrumento</h2>
          <span className="badge warning">MANUAL DEL FABRICANTE</span>
        </div>
        <p className="muted">
          No hay UUID ni factores precargados. Este adaptador sirve para un
          campo numérico GATT; protocolos cifrados, tramas complejas o Bluetooth
          clásico necesitan un driver específico.
        </p>
        <div className="config-grid">
          <label>
            Nombre del perfil
            <input name="name" required maxLength={150} />
          </label>
          <label>
            Equipo asociado
            <select name="vehicle" required defaultValue="">
              <option value="" disabled>
                Selecciona equipo
              </option>
              {vehicles.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Fabricante
            <input name="manufacturer" required maxLength={100} />
          </label>
          <label>
            Modelo
            <input name="model" required maxLength={100} />
          </label>
          <label className="full-field">
            Referencia del manual / documento
            <input
              name="source"
              required
              minLength={8}
              maxLength={500}
              placeholder="Documento y revisión que definen el formato"
            />
          </label>
          <label className="full-field">
            UUID del servicio (128 bits)
            <input
              name="service"
              required
              pattern="[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
            />
          </label>
          <label className="full-field">
            UUID de la característica (128 bits)
            <input
              name="characteristic"
              required
              pattern="[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
            />
          </label>
          <label>
            Señal
            <select name="signal" required defaultValue="">
              <option value="" disabled>
                Selecciona
              </option>
              <option value="low_pressure">Presión baja</option>
              <option value="high_pressure">Presión alta</option>
              <option value="temperature">Temperatura</option>
              <option value="voltage">Voltaje</option>
                <option value="frequency">Frecuencia</option>
            </select>
          </label>
          <label>
            Unidad y referencia
            <select name="unit" required defaultValue="">
              <option value="" disabled>
                Selecciona según manual
              </option>
              {[
                "psi_g",
                "psi_abs",
                "kPa_g",
                "kPa_abs",
                "bar_g",
                "bar_abs",
                "Hz",
                  "degC",
                "V",
              ].map((unit) => (
                <option key={unit}>{unit}</option>
              ))}
            </select>
          </label>
          <label>
            Formato de bytes
            <select name="encoding" required defaultValue="">
              <option value="" disabled>
                Selecciona
              </option>
              {["uint8", "int16", "uint16", "int32", "uint32", "float32"].map(
                (format) => (
                  <option key={format}>{format}</option>
                ),
              )}
            </select>
          </label>
          <label>
            Orden de bytes
            <select name="endian" required defaultValue="">
              <option value="" disabled>
                Selecciona
              </option>
              <option value="little">Little endian</option>
              <option value="big">Big endian</option>
            </select>
          </label>
          <label>
            Byte inicial
            <input name="byteOffset" type="number" min={0} max={508} required />
          </label>
          <label>
            Factor de escala
            <input
              name="scale"
              type="number"
              min={0.00000001}
              max={1000000}
              step="any"
              required
            />
          </label>
          <label>
            Offset de conversión
            <input
              name="offset"
              type="number"
              min={-1000000}
              max={1000000}
              step="any"
              required
            />
          </label>
        </div>
        <p className="muted">
          Valor interpretado = valor raw × escala + offset. Se guarda un perfil
          nuevo e inmutable; no modifica el instrumento.
        </p>
        <button disabled={busy || connected || !canWrite || !vehicles.length}>
          <Save size={15} />
          Guardar perfil de lectura
        </button>
      </form>
    </div>
  );
}
