export default async function DocumentChatPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return (
    <p className="text-sm text-muted-foreground">
      Chat for document {id} coming soon.
    </p>
  );
}
