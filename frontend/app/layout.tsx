import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Career Copilot — AI-Powered Job Fit Analyzer",
  description:
    "An LLM-orchestrated agent that finds roles you're a genuine fit for, explains skill gaps, and gets smarter with your feedback.",
  keywords: ["career", "job search", "AI", "ML", "resume", "fit score"],
  openGraph: {
    title: "Career Copilot",
    description: "Find roles you actually fit. Understand what you're missing. Get better with feedback.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="antialiased">
        <div className="bg-glow" aria-hidden="true" />
        <div className="relative z-10">{children}</div>
      </body>
    </html>
  );
}
