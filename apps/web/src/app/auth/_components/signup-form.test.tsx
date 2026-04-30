import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SignupForm } from "./signup-form";

describe("SignupForm", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllEnvs();
  });

  it("submits signup data to the API and shows the verification notice", async () => {
    const fetchMock = vi.fn(async () =>
      response(201, {
        data: { user: { id: 1, email: "user@example.com", email_verified: false } },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    render(<SignupForm />);

    fireEvent.change(screen.getByLabelText("이메일"), { target: { value: "user@example.com" } });
    fireEvent.change(screen.getByLabelText("비밀번호"), { target: { value: "password1" } });
    fireEvent.change(screen.getByLabelText("이름"), { target: { value: "박지원" } });
    fireEvent.click(screen.getByRole("button", { name: "가입하기" }));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/auth/signup",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({
            email: "user@example.com",
            password: "password1",
            display_name: "박지원",
            locale: "ko",
            turnstile_token: "dev-token",
          }),
        }),
      ),
    );
    expect(await screen.findByText("인증 메일을 확인해 주세요.")).toBeInTheDocument();
  });

  it("shows API validation errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        response(400, {
          code: "validation_error",
          detail: "비밀번호는 8자 이상이며 숫자를 포함해야 합니다.",
        }),
      ),
    );

    render(<SignupForm />);

    fireEvent.change(screen.getByLabelText("이메일"), { target: { value: "user@example.com" } });
    fireEvent.change(screen.getByLabelText("비밀번호"), { target: { value: "password" } });
    fireEvent.click(screen.getByRole("button", { name: "가입하기" }));

    expect(await screen.findByText("비밀번호는 8자 이상이며 숫자를 포함해야 합니다.")).toBeInTheDocument();
  });

  it("uses a Turnstile response token when the widget provides one", async () => {
    const fetchMock = vi.fn(async () =>
      response(201, {
        data: { user: { id: 1, email: "user@example.com", email_verified: false } },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);
    vi.stubEnv("NEXT_PUBLIC_TURNSTILE_SITE_KEY", "site-key");

    render(<SignupForm />);

    fireEvent.change(screen.getByLabelText("이메일"), { target: { value: "user@example.com" } });
    fireEvent.change(screen.getByLabelText("비밀번호"), { target: { value: "password1" } });
    await waitFor(() => expect(window.vaultixOnTurnstileVerified).toBeTypeOf("function"));
    act(() => {
      window.vaultixOnTurnstileVerified?.("turnstile-response");
    });
    await waitFor(() =>
      expect(document.querySelector<HTMLInputElement>('input[name="turnstile_token"]')?.value).toBe(
        "turnstile-response",
      ),
    );
    fireEvent.click(screen.getByRole("button", { name: "가입하기" }));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/auth/signup",
        expect.objectContaining({
          body: JSON.stringify({
            email: "user@example.com",
            password: "password1",
            display_name: "",
            locale: "ko",
            turnstile_token: "turnstile-response",
          }),
        }),
      ),
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
