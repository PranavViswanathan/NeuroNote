import { LoginForm } from "./LoginForm";

interface LoginPageProps {
  searchParams: Record<string, string | string[] | undefined>;
}

export default function LoginPage({ searchParams }: LoginPageProps) {
  const raw = searchParams.next;
  const next = typeof raw === "string" && raw.startsWith("/") ? raw : "/";
  return <LoginForm next={next} />;
}
