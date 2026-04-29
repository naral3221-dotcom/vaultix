import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import SignInPage from "./signin/page";
import SignUpPage from "./signup/page";
import VerifyPage from "./verify/page";

describe("auth pages", () => {
  it("renders the signup form shell", () => {
    render(<SignUpPage />);

    expect(screen.getByRole("heading", { name: "회원가입" })).toBeInTheDocument();
    expect(screen.getByLabelText("이메일")).toBeInTheDocument();
    expect(screen.getByLabelText("비밀번호")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "가입하기" })).toBeInTheDocument();
  });

  it("renders the signin form shell", () => {
    render(<SignInPage />);

    expect(screen.getByRole("heading", { name: "로그인" })).toBeInTheDocument();
    expect(screen.getByLabelText("이메일")).toBeInTheDocument();
    expect(screen.getByLabelText("비밀번호")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "로그인" })).toBeInTheDocument();
  });

  it("renders the email verification form shell", () => {
    render(<VerifyPage searchParams={{ token: "abc" }} />);

    expect(screen.getByRole("heading", { name: "이메일 인증" })).toBeInTheDocument();
    expect(screen.getByLabelText("인증 토큰")).toHaveValue("abc");
    expect(screen.getByRole("button", { name: "이메일 인증하기" })).toBeInTheDocument();
  });
});
