import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AI Character Conversation Pipeline",
  description: "Script-in, video-out production dashboard",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
