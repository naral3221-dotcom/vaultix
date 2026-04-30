import { AuthShell } from "../_components/auth-shell";
import { SigninForm } from "../_components/signin-form";

export default function SignInPage() {
  return (
    <AuthShell
      title="로그인"
      description="저장한 세션으로 다운로드와 계정 기능을 이어갑니다."
      submitLabel="로그인"
      form={<SigninForm />}
      footer={
        <p>
          계정이 없나요? <a href="/auth/signup">회원가입</a>
        </p>
      }
    />
  );
}
