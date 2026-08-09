import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ContextIq1 // Advanced AI Multi-Tenant Workspace",
  description: "Enterprise-grade multi-tenant Agentic RAG client cockpit.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full scroll-smooth antialiased">
      <body className="h-full bg-slate-950 font-sans text-slate-50 selection:bg-emerald-500/30 selection:text-emerald-300">
        <div className="relative flex min-h-screen flex-col overflow-hidden">
          {/* Subtle Ambient Cloud Background Grid */}
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#0f172a_1px,transparent_1px),linear-gradient(to_bottom,#0f172a_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] opacity-25" />
          
          {/* Main Application Work Content Viewport */}
          <div className="relative z-10 flex flex-1 flex-col">
            {children}
          </div>
        </div>
      </body>
    </html>
  );
}