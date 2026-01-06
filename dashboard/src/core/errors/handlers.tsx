// dashboard/src/core/errors/handlers.tsx
import { ActionPanel, Action, Detail } from "@raycast/api";

export function handleBackendError(error: unknown, _t0: number) {
  if (error instanceof TypeError && error.message.includes("fetch")) {
    return (
      <Detail
        markdown={`## Backend DSPy is not running\n\nStart it:\n\`\`\`bash\nmake dev\n\`\`\``}
        actions={
          <ActionPanel>
            <Action.OpenInBrowser title="Open Documentation" url="https://developers.raycast.com" />
          </ActionPanel>
        }
      />
    );
  }

  // Extract error details
  const cause =
    error && typeof error === "object" && "cause" in error ? (error as { cause: unknown }).cause : undefined;
  const causeMessage = cause ? `\n\n**Cause:**\n\`\`\`\n${cause}\n\`\`\`` : "";

  return <Detail markdown={`## Error\n\n${error}${causeMessage}`} />;
}

export function NoInputDetail() {
  return (
    <Detail
      markdown="## No Input Found\n\nSelect text in any app, or copy text to clipboard, then run this command."
      actions={
        <ActionPanel>
          <Action.OpenInBrowser title="Learn About Raycast Extensions" url="https://developers.raycast.com" />
        </ActionPanel>
      }
    />
  );
}
