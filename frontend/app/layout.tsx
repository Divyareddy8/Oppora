import "./globals.css";

export const metadata = {
  title: "Opportunity Radar",
  description: "Personalized opportunities for students and professionals",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
