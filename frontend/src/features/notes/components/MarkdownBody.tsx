import type { ComponentPropsWithoutRef } from "react";
import { createContext, useContext } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { cn } from "@/lib/cn";

/**
 * Renders `body_md` through `react-markdown` mapped onto the Neon Syndicate
 * tokens. GFM task-list checkboxes get a real, wired-up
 * `<input type="checkbox">` in place of the library's default disabled one.
 *
 * The line-index plumbing is the subtle part: `react-markdown` gives the
 * `li` component a `node.position` (1-based source line), but the nested
 * `input` component it renders for a checkbox does NOT carry that position
 * itself — only the checked/disabled flags. So `li` computes the zero-based
 * `line_index` (`start.line - 1`) and threads it to its `input` child via
 * context; getting this off by one silently toggles the wrong line, see
 * `MarkdownBody.test.tsx`.
 */
const LineIndexContext = createContext<number | null>(null);

export function MarkdownBody({
  body,
  onToggleCheckbox,
}: {
  body: string;
  onToggleCheckbox: (lineIndex: number, checked: boolean) => void;
}) {
  return (
    <div className="flex flex-col gap-3 font-body text-body-md text-on-surface [&_.task-list-item]:list-none [&_.task-list-item]:pl-0 [&_ol]:list-decimal [&_ol]:pl-5 [&_ul]:list-disc [&_ul]:pl-5">
      <Markdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: (props) => <HeadingLine level={1} {...props} />,
          h2: (props) => <HeadingLine level={2} {...props} />,
          h3: (props) => <HeadingLine level={3} {...props} />,
          blockquote: (props) => (
            <blockquote
              className="border-l-2 border-neon-pink bg-neon-pink/10 py-2 pl-4 text-on-surface-variant"
              {...props}
            />
          ),
          a: (props) => (
            <a className="text-neon-lime underline hover:text-neon-yellow" {...props} />
          ),
          pre: (props) => (
            <pre
              className="clip-chamfer overflow-x-auto border border-outline-variant bg-surface-container-lowest p-3 font-mono text-label-mono text-neon-lime"
              {...props}
            />
          ),
          code: (props) => <code className="font-mono text-neon-lime" {...props} />,
          li: (props) => <TaskListItem {...props} />,
          input: (props) => <CheckboxInput {...props} onToggleCheckbox={onToggleCheckbox} />,
        }}
      >
        {body}
      </Markdown>
    </div>
  );
}

function HeadingLine({
  level,
  children,
  ...rest
}: ComponentPropsWithoutRef<"h1"> & { level: 1 | 2 | 3 }) {
  const Tag = `h${level}` as const;
  const size = level === 1 ? "text-title-lg" : level === 2 ? "text-title-md" : "text-title-sm";
  return (
    <Tag
      className={cn("flex items-center gap-2 font-display uppercase text-neon-lime", size)}
      {...rest}
    >
      <span aria-hidden="true">{"{}"}</span>
      {children}
    </Tag>
  );
}

interface LiProps extends ComponentPropsWithoutRef<"li"> {
  node?:
    | {
        position?:
          | {
              start?: { line?: number | undefined } | undefined;
            }
          | undefined;
      }
    | undefined;
}

function TaskListItem({ node, children, ...rest }: LiProps) {
  const isTaskItem = rest.className?.includes("task-list-item") ?? false;
  const startLine = node?.position?.start?.line;
  const lineIndex = isTaskItem && typeof startLine === "number" ? startLine - 1 : null;

  return (
    <li {...rest} className={cn(rest.className, isTaskItem && "flex items-start gap-2")}>
      <LineIndexContext.Provider value={lineIndex}>{children}</LineIndexContext.Provider>
    </li>
  );
}

function CheckboxInput({
  onToggleCheckbox,
  ...rest
}: ComponentPropsWithoutRef<"input"> & {
  onToggleCheckbox: (lineIndex: number, checked: boolean) => void;
}) {
  const lineIndex = useContext(LineIndexContext);

  if (rest.type !== "checkbox" || lineIndex === null) {
    return <input {...rest} disabled />;
  }

  return (
    <input
      type="checkbox"
      checked={Boolean(rest.checked)}
      onChange={(e) => onToggleCheckbox(lineIndex, e.target.checked)}
      className="mt-1 size-4 accent-neon-lime"
      aria-label="Toggle objective"
    />
  );
}
