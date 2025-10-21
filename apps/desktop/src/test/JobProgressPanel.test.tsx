import { render, screen } from "@testing-library/react";

import JobProgressPanel from "../components/JobProgressPanel";
import { JobLogInfo, JobProgressPayload } from "../types";

describe("JobProgressPanel", () => {
  it("renders overall progress and log links", () => {
    const progress: JobProgressPayload = {
      overall_percent: 72,
      files: [
        {
          path: "file-a.jpg",
          index: 1,
          total: 2,
          status: "processing",
          current_step: "cleaning",
          percent: 50,
          steps: [
            { key: "queued", label: "Очередь", status: "completed", percent: 5 },
            { key: "loading", label: "Загрузка", status: "completed", percent: 15 },
          ],
        },
      ],
    };
    const logInfo: JobLogInfo = { ready: true, formats: ["json", "csv"] };

    render(
      <JobProgressPanel
        jobId="abc123"
        status="processing"
        progress={progress}
        logInfo={logInfo}
        apiUrl="http://localhost:8765"
      />,
    );

    expect(screen.getByText(/Текущая задача/i)).toBeInTheDocument();
    expect(screen.getByText(/Общий прогресс: 72%/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Скачать JSON/i })).toHaveAttribute(
      "href",
      expect.stringContaining("/api/jobs/abc123/log"),
    );
    expect(screen.getByRole("link", { name: /Скачать CSV/i })).toHaveAttribute(
      "href",
      expect.stringContaining("format=csv"),
    );
  });

  it("renders nothing without job id", () => {
    const { container } = render(
      <JobProgressPanel
        jobId={null}
        status={null}
        progress={null}
        logInfo={null}
        apiUrl="http://localhost:8765"
      />,
    );
    expect(container).toBeEmptyDOMElement();
  });
});
