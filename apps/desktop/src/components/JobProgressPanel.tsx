import { memo, useMemo } from "react";

import { JobLogInfo, JobProgressFile, JobProgressPayload } from "../types";

type JobProgressPanelProps = {
  jobId: string | null;
  status: string | null;
  progress: JobProgressPayload | null;
  logInfo: JobLogInfo | null;
  createdAt?: string | null;
  completedAt?: string | null;
  apiUrl: string;
};

const statusColor = (status: string | null) => {
  switch (status) {
    case "success":
      return "text-emerald-400";
    case "error":
      return "text-red-400";
    case "processing":
      return "text-amber-300";
    default:
      return "text-slate-400";
  }
};

const stepStatusClasses: Record<string, string> = {
  pending: "bg-slate-600 text-slate-300",
  running: "bg-blue-500/20 text-blue-300",
  completed: "bg-emerald-500/20 text-emerald-300",
  failed: "bg-red-500/20 text-red-300",
  skipped: "bg-slate-700/50 text-slate-400",
};

const formatTimestamp = (value?: string | null) => {
  if (!value) {
    return null;
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return null;
  }
  return date.toLocaleString();
};

const renderFileSteps = (file: JobProgressFile) => (
  <div key={`${file.path}-${file.index}`} className="space-y-3 rounded-xl border border-slate-800 bg-slate-950/60 p-4">
    <div className="flex flex-col gap-1">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-sm font-medium text-slate-200 break-all">{file.path}</span>
        <span className="text-xs uppercase tracking-wide text-slate-400">
          {Math.round(file.percent)}%
        </span>
      </div>
      <span className="text-xs text-slate-500">
        Файл {file.index} из {file.total}
      </span>
    </div>
    <div className="grid gap-2 sm:grid-cols-2">
      {file.steps.map((step) => {
        const key = step.status.toLowerCase();
        const baseClass = stepStatusClasses[key] ?? stepStatusClasses.pending;
        return (
          <div key={`${file.path}-${step.key}`} className={`rounded-lg border border-slate-800 px-3 py-2 ${baseClass}`}>
            <div className="flex items-center justify-between gap-2">
              <span className="text-xs font-semibold uppercase tracking-wide">{step.label}</span>
              <span className="text-[10px] uppercase text-slate-400">{step.status}</span>
            </div>
            {step.detail && <p className="mt-1 text-xs text-slate-300">{step.detail}</p>}
          </div>
        );
      })}
    </div>
  </div>
);

const JobProgressPanel = memo(
  ({ jobId, status, progress, logInfo, apiUrl, createdAt, completedAt }: JobProgressPanelProps) => {
    const createdLabel = useMemo(() => formatTimestamp(createdAt), [createdAt]);
    const completedLabel = useMemo(() => formatTimestamp(completedAt), [completedAt]);

    if (!jobId) {
      return null;
    }

    const overall = Math.round(progress?.overall_percent ?? 0);
    const progressWidth = `${Math.min(Math.max(overall, 0), 100)}%`;

    return (
      <section className="space-y-4 rounded-xl border border-slate-800 bg-slate-900/60 p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="space-y-1">
            <h2 className="text-lg font-semibold text-slate-100">Текущая задача</h2>
            <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500">
              <span className="break-all">ID: {jobId}</span>
              {createdLabel && <span>Создана: {createdLabel}</span>}
              {completedLabel && <span>Завершена: {completedLabel}</span>}
            </div>
          </div>
          <span className={`text-xs uppercase tracking-wide ${statusColor(status)}`}>
            {status ?? "pending"}
          </span>
        </div>

        <div>
          <div className="h-2 w-full rounded-full bg-slate-800">
            <div
              className="h-2 rounded-full bg-emerald-500 transition-all duration-300"
              style={{ width: progressWidth }}
            />
          </div>
          <p className="mt-2 text-xs text-slate-400">Общий прогресс: {overall}%</p>
        </div>

        {progress?.files?.length ? (
          <div className="space-y-3">
            {progress.files.map((file) => renderFileSteps(file))}
          </div>
        ) : (
          <p className="text-sm text-slate-400">Ожидание начала обработки файлов…</p>
        )}

        {logInfo?.ready && jobId && (
          <div className="flex flex-wrap items-center gap-3 text-sm text-slate-300">
            <span className="text-xs uppercase tracking-wide text-slate-500">Журнал обработки:</span>
            {logInfo.formats.includes("json") && (
              <a
                className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-1 text-xs font-medium text-emerald-300 hover:border-emerald-500 hover:text-emerald-200"
                href={`${apiUrl}/api/jobs/${jobId}/log`}
                target="_blank"
                rel="noreferrer"
              >
                Скачать JSON
              </a>
            )}
            {logInfo.formats.includes("csv") && (
              <a
                className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-1 text-xs font-medium text-blue-300 hover:border-blue-500 hover:text-blue-200"
                href={`${apiUrl}/api/jobs/${jobId}/log?format=csv`}
                target="_blank"
                rel="noreferrer"
              >
                Скачать CSV
              </a>
            )}
          </div>
        )}
      </section>
    );
  },
);

JobProgressPanel.displayName = "JobProgressPanel";

export default JobProgressPanel;
