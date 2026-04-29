import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { VerifyEmailForm } from "./verify-email-form";

describe("VerifyEmailForm", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("verifies an email token", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => response(200, { data: { verified: true, user_id: 1 } })),
    );

    render(<VerifyEmailForm initialToken="token-123" />);

    fireEvent.click(screen.getByRole("button", { name: "이메일 인증하기" }));

    expect(await screen.findByText("이메일 인증이 완료되었습니다.")).toBeInTheDocument();
  });

  it("shows invalid token errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        response(410, {
          code: "verification_token_invalid",
          detail: "인증 링크가 만료되었거나 이미 사용되었습니다.",
        }),
      ),
    );

    render(<VerifyEmailForm initialToken="expired" />);

    fireEvent.click(screen.getByRole("button", { name: "이메일 인증하기" }));

    expect(await screen.findByText("인증 링크가 만료되었거나 이미 사용되었습니다.")).toBeInTheDocument();
  });
});

function response(status: number, body: unknown) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response;
}
