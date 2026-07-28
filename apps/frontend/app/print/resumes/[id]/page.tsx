// Minimal test page to diagnose print route 500
export default async function PrintResumePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return (
    <div style={{ background: 'white', padding: '20px', fontFamily: 'Arial' }}>
      <p>Print page working. Resume ID: {id}</p>
    </div>
  );
}
