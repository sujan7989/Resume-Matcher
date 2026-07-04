import '@/app/(default)/css/globals.css';

export default function PrintLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-white m-0 p-0">
        {children}
      </body>
    </html>
  );
}
