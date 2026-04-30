import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SigninForm } from "./signin-form";

describe("SigninForm", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("logs in and redirects to explore", async () => {
    const assign = vi.fn();
    vi.stubGlobal("location", { assign });
    const fetchMock = vi.fn(async () =>
      response(200, {
        data: { user: { id: 1, email: "user@example.com", email_verified: true } },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    render(<SigninForm />);

    fireEvent.change(screen.getByLabelText("이메일"), { target: { value: "user@example.com" } });
    fireEvent.change(screen.getByLabelText("비밀번호"), { target: { value: "password1" } });
    fireEvent.click(screen.getByRole("button", { name: "로그인" }));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/auth/login",
        expect.objectContaining({
          method: "POST",
          credentials: "include",
          body: JSON.stringify({ email: "user@example.com", password: "password1" }),
        }),
      ),
    );
    expect(assign).toHaveBeenCalledWith("/explore");
  });

  it("shows login errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        response(401, {
          code: "unauthenticated",
          detail: "이메일 또는 비밀번호가 올바르지 않습니다.",
        }),
      ),
    );

    render(<SigninForm />);

    fireEvent.change(screen.getByLabelText("이메일"), { target: { value: "user@example.com" } });
    fireEvent.change(screen.getByLabelText("비밀번호"), { target: { value: "wrong-password1" } });
    fireEvent.click(screen.getByRole("button", { name: "로그인" }));

    expect(await screen.findByText("이메일 또는 비밀번호가 올바르지 않습니다.")).toBeInTheDocument();
  });

  it("links to Google OAuth login", () => {
    render(<SigninForm />);

    expect(screen.getByRole("link", { name: "Google로 계속하기" })).toHaveAttribute(
      "href",
      "/api/v1/auth/google/start",
    );
  });
});

function response(status: number, body: unknown) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response;
}
