import { FormEvent, useEffect, useRef, useState } from "react";

const API_URL = "http://127.0.0.1:8765";

type ProcessResult = {
  path: string;
  status: string;
  message: string;
};

type MetadataField = {
  key: string;
  category: string;
  name_key: string;
  description_key: string;
  result_fields: string[];
  default_remove: boolean;
  priority: number;
};

type MetadataCatalogueItem = {
  file_type: string;
  fields: MetadataField[];
};

type SettingsSchema = {
  defaults: Record<string, unknown>;
  file_type_defaults: Record<string, Record<string, boolean>>;
  theme_options: string[];
  language_options: string[];
  output_modes: string[];
};

function App() {
  const [connectionStatus, setConnectionStatus] = useState<"idle" | "connecting" | "connected" | "error">("idle");
  const [language, setLanguage] = useState<string | null>(null);
  const [pathInput, setPathInput] = useState("");
  const [results, setResults] = useState<ProcessResult[]>([]);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [metadataCatalogue, setMetadataCatalogue] = useState<MetadataCatalogueItem[]>([]);
  const [metadataCategories, setMetadataCategories] = useState<string[]>([]);
  const [settingsSchema, setSettingsSchema] = useState<SettingsSchema | null>(null);

  const socketRef = useRef<WebSocket | null>(null);

  const resetJobState = () => {
    setJobId(null);
    setJobStatus(null);
    setResults([]);
  };

  const stopWebSocket = () => {
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }
  };

  const fetchCatalogue = async () => {
    const response = await fetch(`${API_URL}/api/metadata/fields`);
    if (!response.ok) {
      throw new Error("Не удалось загрузить каталог метаданных");
    }
    const payload = await response.json();
    setMetadataCatalogue(payload.items ?? []);
    setMetadataCategories(payload.categories ?? []);
  };

  const fetchSettingsSchema = async () => {
    const response = await fetch(`${API_URL}/api/settings/schema`);
    if (!response.ok) {
      throw new Error("Не удалось загрузить схему настроек");
    }
    const payload = (await response.json()) as SettingsSchema;
    setSettingsSchema(payload);
  };

  const fetchSettings = async () => {
    const response = await fetch(`${API_URL}/api/settings`);
    if (!response.ok) {
      throw new Error("Failed to load settings");
    }
    const data = await response.json();
    setLanguage(data.settings?.language ?? null);
  };

  const startWebSocket = (id: string) => {
    stopWebSocket();
    const ws = new WebSocket(`ws://127.0.0.1:8765/ws/jobs/${id}`);
    socketRef.current = ws;
    setJobId(id);
    setJobStatus("pending");
    setResults([]);

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data ?? "{}");
        setJobStatus(payload.status ?? null);
        const normalized: ProcessResult[] = (payload.results ?? []).map((item: any) => ({
          path: String(item.path ?? ""),
          status: String(item.status ?? "unknown"),
          message: String(item.message ?? ""),
        }));
        setResults(normalized);
        if (payload.status === "success" || payload.status === "error") {
          stopWebSocket();
        }
      } catch (err) {
        console.error(err);
      }
    };

    ws.onerror = () => {
      setError("Ошибка WebSocket: не удалось получить обновления статуса.");
      stopWebSocket();
    };

    ws.onclose = () => {
      socketRef.current = null;
    };
  };

  useEffect(() => {
    return () => {
      stopWebSocket();
    };
  }, []);

  const handlePing = async () => {
    setConnectionStatus("connecting");
    setError(null);
    try {
      const response = await fetch(`${API_URL}/health`);
      if (!response.ok) {
        throw new Error("Backend responded with an error");
      }
      await Promise.all([fetchSettings(), fetchSettingsSchema(), fetchCatalogue()]);
      setConnectionStatus("connected");
    } catch (err) {
      console.error(err);
      stopWebSocket();
      resetJobState();
      setConnectionStatus("error");
      setLanguage(null);
      setMetadataCatalogue([]);
      setSettingsSchema(null);
      setError("Не удалось подключиться к backend. Проверьте, что приложение запущено.");
    }
  };

  const handleProcess = async (event: FormEvent) => {
    event.preventDefault();
    const paths = pathInput
      .split("
")
      .map((item) => item.trim())
      .filter(Boolean);

    if (paths.length === 0) {
      setError("Укажите хотя бы один путь к файлу.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/api/jobs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ paths }),
      });

      if (!response.ok) {
        throw new Error("Processing request failed");
      }

      const data = await response.json();
      if (!data.job_id) {
        throw new Error("Missing job id in response");
      }
      startWebSocket(String(data.job_id));
    } catch (err) {
      console.error(err);
      stopWebSocket();
      resetJobState();
      setError("Не удалось отправить файлы на обработку.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center py-16 px-6 gap-6">
      <img src="/logo.svg" alt="Metadata Cleaner" className="h-14" />
      <div className="max-w-5xl w-full space-y-6">
        <header className="space-y-2 text-center">
          <h1 className="text-3xl font-semibold tracking-tight">Metadata Cleaner (Tauri + React)</h1>
          <p className="text-slate-400">
            Состояние backend: {connectionStatus === "connected" && language ? `язык интерфейса — ${language}` : connectionStatus}
          </p>
        </header>

        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <span className="text-sm text-slate-400">
              Подключение: <strong>{connectionStatus}</strong>
            </span>
            <button
              type="button"
              onClick={handlePing}
              className="px-4 py-2 rounded bg-emerald-500 text-white font-medium hover:bg-emerald-600 transition"
            >
              Проверить подключение
            </button>
          </div>

          <form onSubmit={handleProcess} className="space-y-4">
            <label htmlFor="paths" className="block text-sm font-medium text-slate-300">
              Пути к файлам (каждый с новой строки)
            </label>
            <textarea
              id="paths"
              className="w-full min-h-[120px] rounded-lg bg-slate-950 border border-slate-800 text-slate-100 px-3 py-2 focus:outline-none focus:ring focus:ring-emerald-500/40"
              value={pathInput}
              onChange={(event) => setPathInput(event.target.value)}
              placeholder="/Users/alice/photo.jpg"
            />
            <button
              type="submit"
              disabled={
                loading ||
                connectionStatus !== "connected" ||
                jobStatus === "pending" ||
                jobStatus === "processing"
              }
              className="px-4 py-2 rounded bg-blue-500 disabled:bg-blue-500/50 text-white font-medium hover:bg-blue-600 transition"
            >
              {loading ? "Обработка..." : "Очистить метаданные"}
            </button>
          </form>

          {error && <p className="text-sm text-red-400">{error}</p>}
        </div>

        {jobId && (
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4 space-y-2">
            <div className="flex items-center justify-between gap-3">
              <span className="text-sm text-slate-400">Задача</span>
              <code className="text-xs bg-slate-950/80 border border-slate-800 rounded px-2 py-1 text-slate-300">
                {jobId}
              </code>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span className="text-sm text-slate-400">Статус</span>
              <span
                className={`text-xs uppercase tracking-wide ${
                  jobStatus === "success"
                    ? "text-emerald-400"
                    : jobStatus === "error"
                    ? "text-red-400"
                    : "text-amber-300"
                }`}
              >
                {jobStatus ?? "pending"}
              </span>
            </div>
            {jobStatus && !["success", "error"].includes(jobStatus) && (
              <p className="text-xs text-slate-500">Задача выполняется, обновления приходят в реальном времени.</p>
            )}
          </div>
        )}

        {results.length > 0 && (
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 space-y-3">
            <h2 className="text-lg font-semibold text-slate-100">Результаты</h2>
            <ul className="space-y-2 max-h-72 overflow-y-auto pr-2">
              {results.map((item) => (
                <li
                  key={`${item.path}-${item.status}`}
                  className="flex flex-col gap-1 rounded-lg border border-slate-800 bg-slate-950/80 px-4 py-3"
                >
                  <span className="text-sm font-medium text-slate-200">{item.path}</span>
                  <span
                    className={`text-xs uppercase tracking-wide ${
                      item.status === "success"
                        ? "text-emerald-400"
                        : item.status === "error"
                        ? "text-red-400"
                        : "text-amber-300"
                    }`}
                  >
                    {item.status}
                  </span>
                  <span className="text-sm text-slate-400">{item.message}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {metadataCatalogue.length > 0 && (
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-100">Каталог метаданных</h2>
              <span className="text-xs text-slate-500">Категорий: {metadataCategories.length}</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {metadataCatalogue.map((item) => (
                <div key={item.file_type} className="rounded-lg border border-slate-800 bg-slate-950/70 p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold text-slate-200 uppercase">{item.file_type}</span>
                    <span className="text-xs text-slate-500">Полей: {item.fields.length}</span>
                  </div>
                  <ul className="space-y-1 max-h-32 overflow-y-auto pr-1 text-xs text-slate-400">
                    {item.fields.slice(0, 6).map((field) => (
                      <li key={field.key} className="flex justify-between gap-2">
                        <span>{field.key}</span>
                        <span className="text-slate-500">{field.category}</span>
                      </li>
                    ))}
                    {item.fields.length > 6 && <li className="text-slate-500">…</li>}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        )}

        {settingsSchema && (
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6 space-y-3">
            <h2 className="text-lg font-semibold text-slate-100">Параметры приложения</h2>
            <div className="flex flex-wrap gap-3 text-xs text-slate-400">
              <span>Темы: {settingsSchema.theme_options.join(", ")}</span>
              <span>Языки: {settingsSchema.language_options.join(", ")}</span>
              <span>Режимы вывода: {settingsSchema.output_modes.join(", ")}</span>
            </div>
            <div className="text-xs text-slate-500">
              Профиль очистки по умолчанию для изображений: {Object.keys(settingsSchema.file_type_defaults.image || {}).length} полей
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
