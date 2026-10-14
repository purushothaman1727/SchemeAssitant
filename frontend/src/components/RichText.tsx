import { Fragment } from "react";

const TOKEN = /(\*\*[^*\n]+\*\*|\[[ES]\d+\])/g;

/**
 * Renders the small subset of formatting the assistant produces: **bold** and [S1]/[E1]
 * citation tags. Everything is rendered as React text nodes (never as HTML), so model or
 * document output cannot inject markup.
 */
export default function RichText({ text }: { text: string }) {
  return (
    <>
      {text.split(TOKEN).map((part, i) => {
        if (/^\*\*[^*\n]+\*\*$/.test(part)) return <strong key={i}>{part.slice(2, -2)}</strong>;
        if (/^\[[ES]\d+\]$/.test(part)) {
          return (
            <sup key={i} className="mx-0.5 px-1 rounded bg-blue-100 text-blue-900 text-[0.7rem] font-semibold">
              {part.slice(1, -1)}
            </sup>
          );
        }
        return <Fragment key={i}>{part}</Fragment>;
      })}
    </>
  );
}
