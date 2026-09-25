import type { ReactNode } from "react";

export const metadata = { title: "Blog article writer" };

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: "system-ui, sans-serif", maxWidth: 720, margin: "2rem auto", padding: "0 1rem" }}>{children}</body>
    </html>
  );
}
