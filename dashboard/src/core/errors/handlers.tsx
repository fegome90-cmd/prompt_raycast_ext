// dashboard/src/core/errors/handlers.tsx
import { ActionPanel, Action, Detail } from "@raycast/api";

export function handleBackendError(error: unknown, t0: number) {
  const t_copy = Date.now();
  const ttv_ms = t_copy - t0;

  if (error instanceof TypeError && error.message.includes("fetch")) {
    // Backend unavailable
    return (
      <Detail
        markdown={`## Backend DSPy is not running\n\nStart it:\n\`\`\`bash\nmake dev\n\`\`\``}
        actions={
          <ActionPanel>
            <Action.OpenInBrowser
              title="Open Documentation"
              url="https://developers.raycast.com"
            />
          </ActionPanel>
        }
      />
    );
  }

  // Other errors
  return <Detail markdown={`## Error\n\n${error}`} />;
}

export function NoInputDetail() {
  return (
    <Detail
      markdown="## No Input Found\n\nSelect text in any app, or copy text to clipboard, then run this command."
      actions={
        <ActionPanel>
          <Action.OpenInBrowser
            title="Learn About Raycast Extensions"
            url="https://developers.raycast.com"
          />
        </ActionPanel>
      }
    />
  );
}
