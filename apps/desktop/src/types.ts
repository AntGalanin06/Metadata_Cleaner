export type JobProgressStep = {
  key: string;
  label: string;
  status: string;
  percent: number;
  detail?: string | null;
};

export type JobProgressFile = {
  path: string;
  index: number;
  total: number;
  status: string;
  current_step?: string | null;
  percent: number;
  steps: JobProgressStep[];
};

export type JobProgressPayload = {
  overall_percent: number;
  files: JobProgressFile[];
};

export type JobLogInfo = {
  ready: boolean;
  formats: string[];
};
