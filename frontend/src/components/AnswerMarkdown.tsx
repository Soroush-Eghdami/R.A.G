import type { ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type Props = {
  text: string;
  onCite: (n: number) => void;
};

/** Renders an answer and turns [1] into a clickable citation. */
export default function AnswerMarkdown({ text, onCite }: Props) {
  // Negative lookahead keeps real markdown links like [1](url) intact.
  const prepared = text.replace(/\[(\d{1,2})\](?!\()/g, "[cite-$1](#cite-$1)");

  return (
    <div className="markdown text-[0.95rem] leading-relaxed text-ink">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ href, children }) => {
            const cite = href?.match(/^#cite-(\d+)$/);
            if (cite) {
              return (
                <button
                  type="button"
                  onClick={() => onCite(Number(cite[1]))}
                  title={`Source ${cite[1]}`}
                  className="mx-0.5 inline-flex min-w-6 cursor-pointer items-center justify-center rounded-md bg-accent/12 px-1.5 py-0.5 text-xs font-semibold text-accent ring-1 ring-inset ring-accent/25 transition hover:bg-accent/20"
                >
                  [{cite[1]}]
                </button>
              );
            }
            return (
              <a
                href={href}
                target="_blank"
                rel="noreferrer"
                className="font-medium text-primary underline decoration-primary/30 hover:decoration-primary"
              >
                {children}
              </a>
            );
          },
          p: ({ children }) => <p>{children}</p>,
          strong: ({ children }) => <strong className="font-semibold text-ink">{children}</strong>,
          em: ({ children }) => <em className="text-ink/90">{children}</em>,
          ul: ({ children }) => (
            <ul className="list-disc space-y-1 pl-5 marker:text-muted">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal space-y-1 pl-5 marker:text-muted">{children}</ol>
          ),
          li: ({ children }) => <li className="pl-0.5">{children}</li>,
          h1: ({ children }) => (
            <h1 className="text-base font-semibold text-ink">{children}</h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-base font-semibold text-ink">{children}</h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-sm font-semibold text-ink">{children}</h3>
          ),
          blockquote: ({ children }) => (
            <blockquote className="border-l-2 border-primary/40 pl-3 text-muted">
              {children}
            </blockquote>
          ),
          pre: ({ children }) => (
            <pre className="overflow-x-auto rounded-xl border border-line bg-app p-3 text-xs">
              {children}
            </pre>
          ),
          code: ({ children }) => (
            <code className="rounded-md bg-elevated px-1.5 py-0.5 font-mono text-[0.85em] text-ink">
              {children}
            </code>
          ),
          table: ({ children }) => <TableWrap>{children}</TableWrap>,
          th: ({ children }) => (
            <th className="border-b border-line px-2 py-1.5 text-left font-medium text-muted">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="border-b border-line/60 px-2 py-1.5">{children}</td>
          ),
          hr: () => <hr className="border-line" />,
        }}
      >
        {prepared}
      </ReactMarkdown>
    </div>
  );
}

function TableWrap({ children }: { children: ReactNode }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-line">
      <table className="w-full text-xs">{children}</table>
    </div>
  );
}
