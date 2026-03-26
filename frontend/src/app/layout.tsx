import type { Metadata } from "next";

import "../styles/globals.css";

export const metadata: Metadata = {
  title: "ShopPilot",
  description: "Multimodal shopping assistant MVP",
  icons: {
    icon: "/logos/logo2-flat.png",
    shortcut: "/logos/logo2-flat.png",
    apple: "/logos/logo2-flat.png",
  },
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
