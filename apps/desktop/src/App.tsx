import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

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

type Profile = {
  id: string;
  name: string;
  description?: string | null;
  file_type_settings: Record<string, Record<string, boolean>>;
  created_at: string;
  updated_at: string;
};

type ProfileSnapshot = {
  profiles: Profile[];
  active_id: string | null;
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

  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [activeProfileId, setActiveProfileId] = useState<string | null>(null);
  const [profileDraft, setProfileDraft] = useState<Profile | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [profileSaving, setProfileSaving] = useState(false);

  const jobSocketRef = useRef<WebSocket | null>(null);
  const profileSocketRef = useRef<WebSocket | null>(null);

  const resetJobState = () => {
    setJobId(null);
    setJobStatus(null);
    setResults([]);
  };

  const stopJobWebSocket = () => {
    if (jobSocketRef.current) {
      jobSocketRef.current.close();
      jobSocketRef.current = null;
    }
  };

  const stopProfileWebSocket = () => {
    if (profileSocketRef.current) {
      profileSocketRef.current.close();
      profileSocketRef.current = null;
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

  const deepCloneFileTypeSettings = (
    input: Record<string, Record<string, boolean>> | undefined,
  ): Record<string, Record<string, boolean>> => {
    const cloned: Record<string, Record<string, boolean>> = {};
    if (!input) {
      return cloned;
    }
    Object.entries(input).forEach(([fileType, fields]) => {
      cloned[fileType] = { ...fields };
    });
    return cloned;
  };

  const toEditableProfile = (profile: Profile | null): Profile | null => {
    if (!profile) {
      return null;
    }
    return {
      ...profile,
      description: profile.description ?? "",
      file_type_settings: deepCloneFileTypeSettings(profile.file_type_settings),
    };
  };

  const syncProfileState = (snapshot: ProfileSnapshot) => {
    const snapshotProfiles = snapshot.profiles ?? [];
    setProfiles(snapshotProfiles);
    const activeId = snapshot.active_id ?? null;
    setActiveProfileId(activeId);
    const activeProfile = snapshotProfiles.find((item) => item.id === activeId) ?? null;
    setProfileDraft(toEditableProfile(activeProfile));
  };

  const fetchProfiles = async () => {
    const response = await fetch(`${API_URL}/api/settings/profiles`);
    if (!response.ok) {
      throw new Error("Failed to load profiles");
    }
    const payload = (await response.json()) as ProfileSnapshot;
    syncProfileState(payload);
  };

  const defaultProfileSettings = (): Record<string, Record<string, boolean>> => {
    if (settingsSchema?.file_type_defaults) {
      return deepCloneFileTypeSettings(settingsSchema.file_type_defaults);
    }
    if (profiles[0]) {
      return deepCloneFileTypeSettings(profiles[0].file_type_settings);
    }
    return {};
  };

  const handleProfileEvent = (payload: any) => {
    const eventType = String(payload.event ?? "");
    if (!eventType) {
      return;
    }
    const snapshot: ProfileSnapshot = {
      profiles: (payload.profiles ?? []) as Profile[],
      active_id: (payload.active_id ?? null) as string | null,
    };
    syncProfileState(snapshot);
    if (eventType === "profile_created" && payload.profile) {
      setProfileDraft(toEditableProfile(payload.profile as Profile));
      setProfileError(null);
    }
  };

  const startProfileWebSocket = () => {
    stopProfileWebSocket();
    const ws = new WebSocket(`ws://127.0.0.1:8765/ws/settings/profiles`);
    profileSocketRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data ?? "{}");
        handleProfileEvent(payload);
      } catch (err) {
        console.error(err);
      }
    };

    ws.onerror = () => {
      setProfileError("Ошибка WebSocket при загрузке профилей.");
      stopProfileWebSocket();
    };

    ws.onclose = () => {
      profileSocketRef.current = null;
    };
  };

  const handleActivateProfile = async (profileId: string) => {
    if (!profileId) {
      return;
    }
    setProfileError(null);
    try {
      const response = await fetch(
        `${API_URL}/api/settings/profiles/${profileId}/activate`,
        {
          method: "POST",
        },
      );
      if (!response.ok) {
        throw new Error("Failed to activate profile");
      }
      const snapshot = (await response.json()) as ProfileSnapshot;
      syncProfileState(snapshot);
    } catch (err) {
      console.error(err);
      setProfileError("Не удалось активировать профиль.");
    }
  };

  const handleProfileNameChange = (value: string) => {
    setProfileDraft((current) => {
      if (!current) {
        return current;
      }
      return { ...current, name: value };
    });
  };

  const handleProfileDescriptionChange = (value: string) => {
    setProfileDraft((current) => {
      if (!current) {
        return current;
      }
      return { ...current, description: value };
    });
  };

  const handleToggleMetadataField = (fileType: string, key: string) => {
    setProfileDraft((current) => {
      if (!current) {
        return current;
      }
      const existing = current.file_type_settings[fileType] ?? {};
      return {
        ...current,
        file_type_settings: {
          ...current.file_type_settings,
          [fileType]: {
            ...existing,
            [key]: !existing[key],
          },
        },
      };
    });
  };

  const handleProfileSave = async () => {
    if (!profileDraft) {
      return;
    }
    setProfileSaving(true);
    setProfileError(null);
    try {
      const response = await fetch(
        `${API_URL}/api/settings/profiles/${profileDraft.id}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: profileDraft.name,
            description: profileDraft.description?.toString().trim() || null,
            file_type_settings: profileDraft.file_type_settings,
          }),
        },
      );
      if (!response.ok) {
        throw new Error("Failed to save profile");
      }
      const saved = (await response.json()) as Profile;
      setProfileDraft(toEditableProfile(saved));
      setProfileError(null);
    } catch (err) {
      console.error(err);
      setProfileError("Не удалось сохранить профиль.");
    } finally {
      setProfileSaving(false);
    }
  };

  const handleCreateProfile = async () => {
    setProfileError(null);
    try {
      const response = await fetch(`${API_URL}/api/settings/profiles`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: `Профиль ${profiles.length + 1}`,
          file_type_settings: defaultProfileSettings(),
        }),
      });
      if (!response.ok) {
        throw new Error("Failed to create profile");
      }
      const created = (await response.json()) as Profile;
      setProfileDraft(toEditableProfile(created));
    } catch (err) {
      console.error(err);
      setProfileError("Не удалось создать новый профиль.");
    }
  };

  const metadataLookup = useMemo(() => {
    const fileTypeMap = new Map<string, Map<string, MetadataField>>();
    metadataCatalogue.forEach((item) => {
      const fieldMap = new Map<string, MetadataField>();
      item.fields.forEach((field) => {
        fieldMap.set(field.key, field);
      });
      fileTypeMap.set(item.file_type, fieldMap);
    });
    return fileTypeMap;
  }, [metadataCatalogue]);

  const resolveMetadataLabel = (fileType: string, key: string) => {
    const field = metadataLookup.get(fileType)?.get(key);
    return field?.name_key ?? key;
  };

  const startJobWebSocket = (id: string) => {
    stopJobWebSocket();
    const ws = new WebSocket(`ws://127.0.0.1:8765/ws/jobs/${id}`);
    jobSocketRef.current = ws;
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
          stopJobWebSocket();
        }
      } catch (err) {
        console.error(err);
      }
    };

    ws.onerror = () => {
      setError("Ошибка WebSocket: не удалось получить обновления статуса.");
      stopJobWebSocket();
    };

    ws.onclose = () => {
      jobSocketRef.current = null;
    };
  };

  useEffect(() => {
    return () => {
      stopJobWebSocket();
      stopProfileWebSocket();
    };
  }, []);

  useEffect(() => {
    if (connectionStatus === "connected") {
      startProfileWebSocket();
    } else {
      stopProfileWebSocket();
    }
  }, [connectionStatus]);

  const handlePing = async () => {
    setConnectionStatus("connecting");
    setError(null);
    try {
      const response = await fetch(`${API_URL}/health`);
      if (!response.ok) {
        throw new Error("Backend responded with an error");
      }
      await Promise.all([
        fetchSettings(),
        fetchSettingsSchema(),
        fetchCatalogue(),
        fetchProfiles(),
      ]);
      setConnectionStatus("connected");
    } catch (err) {
      console.error(err);
      stopJobWebSocket();
      stopProfileWebSocket();
      resetJobState();
      setConnectionStatus("error");
      setLanguage(null);
      setMetadataCatalogue([]);
      setSettingsSchema(null);
      setProfiles([]);
      setActiveProfileId(null);
      setProfileDraft(null);
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
      startJobWebSocket(String(data.job_id));
    } catch (err) {
      console.error(err);
      stopJobWebSocket();
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

        <section className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-slate-100">Профили очистки</h2>
              <p className="text-sm text-slate-400">Настройте набор полей и активируйте профиль для новых задач.</p>
            </div>
            <button
              type="button"
              onClick={handleCreateProfile}
              disabled={connectionStatus !== "connected"}
              className="px-3 py-2 rounded bg-emerald-500 disabled:bg-emerald-500/40 text-white text-sm font-medium hover:bg-emerald-600 transition"
            >
              Создать профиль
            </button>
          </div>

          {profileError && <p className="text-sm text-red-400">{profileError}</p>}

          <div className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-1">
                <label className="block text-sm font-medium text-slate-300" htmlFor="activeProfile">
                  Активный профиль
                </label>
                <select
                  id="activeProfile"
                  className="w-full rounded-lg bg-slate-950 border border-slate-800 px-3 py-2 text-sm text-slate-100"
                  value={activeProfileId ?? ""}
                  onChange={(event) => handleActivateProfile(event.target.value)}
                  disabled={connectionStatus !== "connected" || profiles.length === 0}
                >
                  <option value="" disabled>
                    {connectionStatus === "connected" ? "Выберите профиль" : "Нет подключения"}
                  </option>
                  {profiles.map((profile) => (
                    <option key={profile.id} value={profile.id}>
                      {profile.name || "Без названия"}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-1">
                <label className="block text-sm font-medium text-slate-300" htmlFor="profileName">
                  Название профиля
                </label>
                <input
                  id="profileName"
                  type="text"
                  value={profileDraft?.name ?? ""}
                  onChange={(event) => handleProfileNameChange(event.target.value)}
                  disabled={!profileDraft}
                  className="w-full rounded-lg bg-slate-950 border border-slate-800 px-3 py-2 text-sm text-slate-100 disabled:text-slate-500"
                  placeholder="Например: Публикация"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="block text-sm font-medium text-slate-300" htmlFor="profileDescription">
                Описание
              </label>
              <input
                id="profileDescription"
                type="text"
                value={profileDraft?.description ?? ""}
                onChange={(event) => handleProfileDescriptionChange(event.target.value)}
                disabled={!profileDraft}
                className="w-full rounded-lg bg-slate-950 border border-slate-800 px-3 py-2 text-sm text-slate-100 disabled:text-slate-500"
                placeholder="Короткое описание профиля"
              />
            </div>

            {profileDraft ? (
              <div className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  {Object.entries(profileDraft.file_type_settings)
                    .sort(([a], [b]) => a.localeCompare(b))
                    .map(([fileType, fields]) => (
                      <div key={fileType} className="rounded-lg border border-slate-800 bg-slate-950/40 p-4 space-y-3">
                        <div className="flex items-center justify-between">
                          <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-300">
                            {fileType}
                          </h3>
                          <span className="text-xs text-slate-500">{Object.keys(fields).length} полей</span>
                        </div>
                        <div className="space-y-2 max-h-52 overflow-y-auto pr-1 custom-scrollbar">
                          {Object.entries(fields)
                            .sort(([a], [b]) => a.localeCompare(b))
                            .map(([fieldKey, enabled]) => (
                              <label
                                key={`${fileType}-${fieldKey}`}
                                className="flex items-start gap-2 text-sm text-slate-200"
                              >
                                <input
                                  type="checkbox"
                                  className="mt-1 h-4 w-4 rounded border-slate-700 bg-slate-900"
                                  checked={Boolean(enabled)}
                                  onChange={() => handleToggleMetadataField(fileType, fieldKey)}
                                />
                                <span>
                                  {resolveMetadataLabel(fileType, fieldKey)}
                                </span>
                              </label>
                            ))}
                        </div>
                      </div>
                    ))}
                </div>

                <div className="flex justify-end">
                  <button
                    type="button"
                    onClick={handleProfileSave}
                    disabled={profileSaving || !profileDraft || connectionStatus !== "connected"}
                    className="px-4 py-2 rounded bg-blue-500 disabled:bg-blue-500/40 text-white text-sm font-medium hover:bg-blue-600 transition"
                  >
                    {profileSaving ? "Сохранение..." : "Сохранить профиль"}
                  </button>
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-400">Подключитесь к backend и выберите профиль для редактирования.</p>
            )}
          </div>
        </section>

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
