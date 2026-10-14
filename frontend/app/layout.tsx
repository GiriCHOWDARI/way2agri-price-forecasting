import type { Metadata } from "next";
import React from "react";

export const metadata: Metadata = {
  title: "Way2Agribusiness Price Forecast",
  description: "Monthly price forecasting prototype dashboard",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body style={{ margin: 0, fontFamily: "Arial, sans-serif", background: "#f6f8fb", color: "#172033" }}>{children}</body></html>;
}
