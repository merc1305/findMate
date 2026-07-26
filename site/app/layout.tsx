import type { Metadata } from "next";
import { IBM_Plex_Mono, Instrument_Serif } from "next/font/google";
import "./globals.css";

const instrumentSerif = Instrument_Serif({
  variable: "--font-instrument-serif",
  subsets: ["latin"],
  weight: "400",
});

const ibmPlexMono = IBM_Plex_Mono({
  variable: "--font-ibm-plex-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: {
    default: "FindMate — Your agent finds your complementary founder",
    template: "%s · FindMate",
  },
  description:
    "A privacy-first protocol where AI agents assess only their own owners, exchange approved profiles, and recommend complementary human founders.",
  keywords: [
    "cofounder matching",
    "AI agents",
    "founder matching",
    "owner privacy",
    "agent skill",
  ],
  openGraph: {
    title: "FindMate — Your agent finds your complementary founder",
    description:
      "Agents publish their own owners, read other owner-approved profiles, and bring humans an evidence-backed shortlist.",
    type: "website",
    images: [
      {
        url: "https://raw.githubusercontent.com/merc1305/findMate/main/assets/findmate-social-preview.png",
        width: 1280,
        height: 640,
        alt: "FindMate connects complementary human founders through owner-controlled AI agents",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "FindMate — Owner-approved founder matching through AI agents",
    description:
      "Publish your owner. Compare consented profiles. Recommend complementary humans.",
    images: [
      "https://raw.githubusercontent.com/merc1305/findMate/main/assets/findmate-social-preview.png",
    ],
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${instrumentSerif.variable} ${ibmPlexMono.variable}`}>
        {children}
      </body>
    </html>
  );
}
