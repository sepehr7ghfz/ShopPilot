import type { Metadata } from "next";

import "../styles/globals.css";

export const metadata: Metadata = {
  title: "ShopPilot",
  description: "Multimodal shopping assistant MVP",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>): JSX.Element {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
