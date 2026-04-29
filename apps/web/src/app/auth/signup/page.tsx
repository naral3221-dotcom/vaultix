import { AuthShell } from "../_components/auth-shell";
import { SignupForm } from "../_components/signup-form";

export default function SignUpPage() {
  return (
    <AuthShell
      title="회원가입"
      description="이메일 인증 후 Vaultix의 이미지 자산을 다운로드할 수 있습니다."
      submitLabel="가입하기"
      form={<SignupForm />}
      footer={
        <p>
          이미 계정이 있나요? <a href="/auth/signin">로그인</a>
        </p>
      }
    />
  );
}
