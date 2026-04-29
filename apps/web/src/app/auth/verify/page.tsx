import { AuthShell } from "../_components/auth-shell";
import { VerifyEmailForm } from "../_components/verify-email-form";

type VerifyPageProps = {
  searchParams?: {
    token?: string;
  };
};

export default function VerifyPage({ searchParams }: VerifyPageProps) {
  return (
    <AuthShell
      title="이메일 인증"
      description="메일로 받은 인증 토큰을 확인해 계정을 활성화합니다."
      submitLabel="이메일 인증하기"
      form={<VerifyEmailForm initialToken={searchParams?.token ?? ""} />}
      footer={
        <p>
          인증 후 <a href="/auth/signin">로그인</a>으로 이동해 주세요.
        </p>
      }
    />
  );
}
