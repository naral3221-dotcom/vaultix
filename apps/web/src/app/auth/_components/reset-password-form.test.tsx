import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ForgotPasswordForm, ResetPasswordForm } from "./reset-password-form";

describe("password reset forms", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("requests a password reset email", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => response(200, { data: { sent: true } })));

    render(<ForgotPasswordForm />);

    fireEvent.change(screen.getByLabelText("이메일"), { target: { value: "user@example.com" } });
    fireEvent.click(screen.getByRole("button", { name: "재설정 메일 받기" }));

    expect(await screen.findByText("비밀번호 재설정 안내를 확인해 주세요.")).toBeInTheDocument();
  });

  it("resets the password with a token", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => response(200, { data: { reset: true } })));

    render(<ResetPasswordForm initialToken="reset-token" />);

    fireEvent.change(screen.getByLabelText("새 비밀번호"), { target: { value: "newpass1" } });
    fireEvent.click(screen.getByRole("button", { name: "비밀번호 변경" }));

    expect(await screen.findByText("비밀번호가 변경되었습니다.")).toBeInTheDocument();
  });
});

function response(status: number, body: unknown) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response;
}
