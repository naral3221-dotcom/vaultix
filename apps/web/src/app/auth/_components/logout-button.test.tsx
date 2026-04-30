import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { LogoutButton } from "./logout-button";

describe("LogoutButton", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("calls logout and redirects home", async () => {
    const assign = vi.fn();
    vi.stubGlobal("location", { assign });
    vi.stubGlobal("fetch", vi.fn(async () => response(200, { data: { logged_out: true } })));

    render(<LogoutButton />);

    fireEvent.click(screen.getByRole("button", { name: "로그아웃" }));

    await waitFor(() => expect(assign).toHaveBeenCalledWith("/"));
  });
});

function response(status: number, body: unknown) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response;
}
