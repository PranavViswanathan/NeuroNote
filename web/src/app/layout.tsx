import type { Metadata } from "next";
import type { ReactNode } from "react";
import "katex/dist/katex.min.css";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "NeuroNote",
    template: "%s | NeuroNote",
  },
  description:
    "Knowledge graph note-taking application with bidirectional linking and entity extraction",
  keywords: ["notes", "knowledge graph", "PKM", "bidirectional links", "entities", "note-taking"],
  authors: [{ name: "NeuroNote Team" }],
  creator: "NeuroNote Team",
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://neuronote.app",
    siteName: "NeuroNote",
    title: "NeuroNote - Knowledge Graph Note-Taking",
    description:
      "Build your personal knowledge graph with bidirectional linking and automatic entity extraction",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "NeuroNote Preview",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "NeuroNote - Knowledge Graph Note-Taking",
    description:
      "Build your personal knowledge graph with bidirectional linking and automatic entity extraction",
    images: ["/og-image.png"],
  },
  robots: {
    index: true,
    follow: true,
  },
  icons: {
    icon: "/favicon.ico",
    shortcut: "/favicon-16x16.png",
    apple: "/apple-touch-icon.png",
  },
  manifest: "/site.webmanifest",
};

interface RootLayoutProps {
  children: ReactNode;
}

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
