type PublicPageShellProps = {
  eyebrow: string;
  title: string;
  description: string;
  children?: React.ReactNode;
};

export function PublicPageShell({ eyebrow, title, description, children }: PublicPageShellProps) {
  return (
    <main className="simple-page">
      <a className="simple-back" href="/">
        Vaultix
      </a>
      <section className="simple-hero">
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        <p>{description}</p>
      </section>
      {children ? <section className="simple-content">{children}</section> : null}
    </main>
  );
}

