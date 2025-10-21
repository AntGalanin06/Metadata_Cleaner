import { render, screen } from "@testing-library/react";

import App from "./App";

describe("App", () => {
  it("renders profile management controls", () => {
    render(<App />);

    expect(screen.getByText(/Профили очистки/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Создать профиль/i })).toBeDisabled();
    expect(screen.getByLabelText(/Активный профиль/i)).toBeDisabled();
  });
});
