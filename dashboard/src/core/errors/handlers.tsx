// dashboard/src/core/errors/handlers.tsx
import { ActionPanel, Action, Detail } from "@raycast/api";
import { tokens } from "../design/tokens";

export function handleBackendError(error: unknown, _t0: number) {
  // Timeout errors
  if (error instanceof Error && error.name === "AbortError") {
    return (
      <Detail
        markdown={`## ${tokens.semantic.error.icon} Request Timed Out\n\nThe backend took too long to respond.\n\n**Try:**\n- Use \`mode:"legacy"\` for faster results\n- Shorten your prompt\n- Check if the backend is overloaded\n\n**Current timeout:** 120s`}
        actions={
          <ActionPanel>
            <Action.OpenInBrowser title="Open Documentation" url="https://developers.raycast.com" />
          </ActionPanel>
        }
      />
    );
  }

  // Connection refused errors
  if (
    error instanceof Error &&
    (error.message.includes("ECONNREFUSED") || error.message.includes("fetch failed") || (error.message.includes("fetch") && error instanceof TypeError))
  ) {
    return (
      <Detail
        markdown={`## ${tokens.semantic.error.icon} Backend Not Running\n\nStart the backend:\n\`\`\`bash\ncd /Users/felipe_gonzalez/Developer/raycast_ext\nmake dev\n\`\`\`\n\nThen verify:\n\`\`\`bash\ncurl http://localhost:8000/health\n\`\`\``}
        actions={
          <ActionPanel>
            <Action.OpenInBrowser title="Open Documentation" url="https://developers.raycast.com" />
          </ActionPanel>
        }
      />
    );
  }

  // Network errors
  if (error instanceof Error && (error.message.includes("ENOTFOUND") || error.message.includes("ERR_CONNECTION"))) {
    return (
      <Detail
        markdown={`## ${tokens.semantic.error.icon} Network Error\n\nCannot reach the backend server.\n\n**Troubleshooting:**\n- Check your internet connection\n- Verify localhost is resolving\n- Check if a firewall is blocking port 8000\n\n**Error:** \`${error.message}\``}
        actions={
          <ActionPanel>
            <Action.OpenInBrowser title="Open Documentation" url="https://developers.raycast.com" />
          </ActionPanel>
        }
      />
    );
  }

  // HTTP errors with status codes
  if (error instanceof Error && error.message.includes("DSPy backend error:")) {
    const match = error.message.match(/DSPy backend error: (\d+)/);
    const status = match ? parseInt(match[1], 10) : null;

    if (status === 504) {
      return (
        <Detail
          markdown={`## ${tokens.semantic.error.icon} Backend Timeout\n\nThe backend request timed out.\n\n**Try:**\n- Use \`mode:"legacy"\` for faster results\n- Shorten your prompt\n- Check backend logs: \`make logs\``}
          actions={
            <ActionPanel>
              <Action.OpenInBrowser title="Open Documentation" url="https://developers.raycast.com" />
            </ActionPanel>
          }
        />
      );
    }

    if (status === 400) {
      return (
        <Detail
          markdown={`## ${tokens.semantic.error.icon} Invalid Request\n\nThe backend rejected the request.\n\n**Common issues:**\n- Prompt must be at least 5 characters\n- Mode must be "legacy" or "nlac"\n\n**Error:** \`${error.message}\``}
          actions={
            <ActionPanel>
              <Action.OpenInBrowser title="Open Documentation" url="https://developers.raycast.com" />
            </ActionPanel>
          }
        />
      );
    }
  }

  // Extract error details
  const cause =
    error && typeof error === "object" && "cause" in error ? (error as { cause: unknown }).cause : undefined;
  const causeMessage = cause ? `\n\n**Cause:**\n\`\`\`\n${cause}\n\`\`\`` : "";

  return <Detail markdown={`## ${tokens.semantic.error.icon} Error\n\n${error}${causeMessage}`} />;
}

export function NoInputDetail() {
  return (
    <Detail
      markdown={`## ${tokens.semantic.info.icon} No Input Found\n\nSelect text in any app, or copy text to clipboard, then run this command.`}
      actions={
        <ActionPanel>
          <Action.OpenInBrowser title="Learn About Raycast Extensions" url="https://developers.raycast.com" />
        </ActionPanel>
      }
    />
  );
}
